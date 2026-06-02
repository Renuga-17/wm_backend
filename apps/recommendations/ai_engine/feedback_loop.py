import logging
from django.core.cache import cache
from apps.recommendations.models import AIDecision, SlottingHistory
from apps.zones.models import Zone
from apps.bins.models import Bin

logger = logging.getLogger(__name__)

# Cache key for AI weights tuning
SLOTTING_WEIGHTS_CACHE_KEY = 'ai_slotting_coefficients'

DEFAULT_WEIGHTS = {
    'proximity_reward_factor': 15.0,
    'congestion_penalty_factor': 5.0,
    'affinity_bonus_factor': 2.0,
    'travel_cost_factor': 0.1
}

class AIFeedbackLoop:
    _local_weights = None

    @classmethod
    def get_current_weights(cls):
        """
        Retrieves current slotting algorithm weights from cache, or returns defaults.
        """
        if cls._local_weights is not None:
            return cls._local_weights.copy()

        try:
            val = cache.get(SLOTTING_WEIGHTS_CACHE_KEY)
            if val:
                cls._local_weights = val
                return val.copy()
        except Exception as e:
            logger.warning(f"Cache get failed (likely Redis down), using default fallback weights: {e}")

        return DEFAULT_WEIGHTS.copy()

    @classmethod
    def process_feedback_signal(cls, signal_type, payload):
        """
        Processes feedback signals to dynamically tune slotting parameters.
        Signals:
          - 'PICK_DURATION': Adjust travel cost factor or congestion penalty.
          - 'RE_SLOT_FREQUENCY': Penalize recommendation volatility.
          - 'CONGESTION_SHIFT': Boost congestion penalty weights.
        """
        weights = cls.get_current_weights()
        adjustment_made = False
        log_message = ""

        # Retrieve the AIDecision to append feedback details if decision_id is provided
        decision_id = payload.get('decision_id')
        decision = None
        if decision_id:
            try:
                decision = AIDecision.objects.get(id=decision_id)
            except (AIDecision.DoesNotExist, ValueError):
                pass

        if signal_type == 'PICK_DURATION':
            duration = float(payload.get('duration', 0.0))
            benchmark = float(payload.get('benchmark', 40.0))
            
            # If duration is significantly higher than benchmark, penalize travel and congestion more
            if duration > benchmark * 1.3:
                weights['travel_cost_factor'] = round(weights['travel_cost_factor'] * 1.05, 4)
                weights['congestion_penalty_factor'] = round(weights['congestion_penalty_factor'] * 1.10, 4)
                adjustment_made = True
                log_message = f"Pick duration ({duration}s) exceeded benchmark ({benchmark}s). Congestion penalty bumped to {weights['congestion_penalty_factor']}"

            # Log to SlottingHistory if matching record is found
            history_id = payload.get('history_id')
            if history_id:
                try:
                    history = SlottingHistory.objects.get(id=history_id)
                    history.pick_time_seconds = duration
                    # calculate efficiency gain (benchmark - duration) / benchmark
                    history.efficiency_gain = (benchmark - duration) / benchmark
                    history.save()
                except (SlottingHistory.DoesNotExist, ValueError):
                    pass

        elif signal_type == 'RE_SLOT_FREQUENCY':
            re_slots_count = int(payload.get('re_slots_count', 0))
            
            # High re-slotting frequency indicates recommendation instability
            if re_slots_count > 5:
                # Lower affinity bonus and proximity factors to stabilize placement recommendations
                weights['proximity_reward_factor'] = max(5.0, round(weights['proximity_reward_factor'] * 0.95, 2))
                weights['affinity_bonus_factor'] = max(1.0, round(weights['affinity_bonus_factor'] * 0.90, 2))
                adjustment_made = True
                log_message = f"High re-slot count ({re_slots_count}). Stabilizing slotting proximity factor to {weights['proximity_reward_factor']}"

        elif signal_type == 'CONGESTION_SHIFT':
            congestion_diff = float(payload.get('congestion_diff', 0.0))
            
            # If congestion increases, make penalty heavier
            if congestion_diff > 0.2:
                weights['congestion_penalty_factor'] = min(15.0, round(weights['congestion_penalty_factor'] * 1.15, 4))
                adjustment_made = True
                log_message = f"Congestion spike detected ({congestion_diff}). Increasing congestion penalty to {weights['congestion_penalty_factor']}"

        if adjustment_made:
            cls._local_weights = weights
            try:
                cache.set(SLOTTING_WEIGHTS_CACHE_KEY, weights, timeout=None)
            except Exception as e:
                logger.warning(f"Cache set failed (likely Redis down): {e}")
            logger.info(f"AI Feedback Loop Adjusted Weights: {log_message}")

        # Update decision record with feedback details
        if decision:
            decision.feedback_received = {
                "signal_type": signal_type,
                "payload": payload,
                "adjusted_weights": weights if adjustment_made else None,
                "log_message": log_message
            }
            decision.save()

        return {
            "success": True,
            "adjustment_made": adjustment_made,
            "current_weights": weights,
            "message": log_message or "Signal processed. Weights remained unchanged."
        }
