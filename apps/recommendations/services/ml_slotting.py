import math
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q
from apps.products.models import Product
from apps.bins.models import Bin
from apps.zones.models import Zone
from apps.movements.models import StockMovement
from apps.warehouses.models import NavigationNode, NavigationEdge, Rack
from apps.recommendations.models import DemandForecast, CongestionPrediction, SlottingScore, AIDecision, AllocationRecommendation
from apps.routes.services.pathfinding import PathfindingService

class AISlottingEngine:
    @staticmethod
    def forecast_demand(product_id_or_sku, days_history=30):
        """
        Calculates demand forecast score (0.0 to 1.0) for an SKU.
        Uses historical StockMovement pick counts, decaying weights over time,
        and falls back to category-level statistics if SKU-level history is sparse.
        """
        try:
            product = Product.objects.get(id=product_id_or_sku)
        except (Product.DoesNotExist, ValueError):
            product = Product.objects.filter(sku=product_id_or_sku).first()
            if not product:
                raise ValueError(f"Product {product_id_or_sku} not found.")

        # Query recent stock movements of type PICK or OUTBOUND
        now = timezone.now()
        start_date = now - timezone.timedelta(days=days_history)
        
        movements = StockMovement.objects.filter(
            product=product,
            moved_at__gte=start_date,
            movement_type__iexact='PICK'
        )
        
        # Calculate daily pick frequency and quantity
        total_picks = movements.count()
        total_qty = movements.aggregate(total=Sum('quantity'))['total'] or 0
        
        # If sparse history, look at category averages
        if total_picks == 0 and product.category:
            cat_movements = StockMovement.objects.filter(
                product__category=product.category,
                moved_at__gte=start_date,
                movement_type__iexact='PICK'
            )
            cat_product_count = Product.objects.filter(category=product.category).count() or 1
            avg_picks_per_prod = cat_movements.count() / cat_product_count
            
            # Category-based heuristic prediction
            predicted_score = min(0.1 + (avg_picks_per_prod / 50.0), 0.95)
        else:
            # SKU-specific decaying heuristic (simulating LightGBM/Prophet trend line)
            # Higher weight to more recent picks
            recent_score = 0.0
            for days_ago in range(days_history):
                day_start = now - timezone.timedelta(days=days_ago + 1)
                day_end = now - timezone.timedelta(days=days_ago)
                daily_picks = movements.filter(moved_at__range=(day_start, day_end)).count()
                
                # Decay factor: 0.95^days_ago (recent days are weighted higher)
                decay = math.pow(0.95, days_ago)
                recent_score += daily_picks * decay
            
            # Normalize to 0.0 - 1.0 range
            predicted_score = min(0.05 + (recent_score / 30.0), 1.0)

        # Log to db
        forecast = DemandForecast.objects.create(
            product=product,
            predicted_demand_score=Decimal(str(round(predicted_score, 4))),
            forecast_period='DAILY',
            confidence_score=Decimal('0.88')
        )
        return forecast

    @staticmethod
    def predict_congestion_risk(warehouse_id):
        """
        Computes the traffic congestion risk (0.0 to 1.0) and volume for all zones.
        Looks at current bin occupancy and recent path traversal frequency.
        """
        zones = Zone.objects.filter(warehouse_id=warehouse_id)
        predictions = []
        
        # Time threshold for recent traffic
        now = timezone.now()
        traffic_start = now - timezone.timedelta(hours=24)
        
        for zone in zones:
            # 1. Capacity occupancy penalty
            total_bins = Bin.objects.filter(shelf__rack__zone=zone).count()
            occupied_bins = Bin.objects.filter(shelf__rack__zone=zone, is_occupied=True).count()
            occupancy_ratio = occupied_bins / total_bins if total_bins > 0 else 0.0
            
            # 2. Movement frequency count
            recent_moves = StockMovement.objects.filter(
                Q(from_bin__shelf__rack__zone=zone) | Q(to_bin__shelf__rack__zone=zone),
                moved_at__gte=traffic_start
            ).count()
            
            # Heuristic calculation for congestion risk probability
            traffic_factor = min(recent_moves / 40.0, 1.0)
            risk_score = 0.4 * occupancy_ratio + 0.6 * traffic_factor
            risk_score = min(max(risk_score, 0.0), 1.0)
            
            # Log prediction
            pred = CongestionPrediction.objects.create(
                zone=zone,
                congestion_risk=Decimal(str(round(risk_score, 4))),
                predicted_traffic_volume=recent_moves
            )
            predictions.append(pred)
            
        return predictions

    @staticmethod
    def optimize_slotting(product_id_or_sku, warehouse_id):
        """
        Determines the operationally optimal bin placement using predictive multi-factor score.
        Considers structural safety, demand proximity, congestion penalty, category affinity, and route cost.
        """
        # Find product
        try:
            product = Product.objects.get(id=product_id_or_sku)
        except (Product.DoesNotExist, ValueError):
            product = Product.objects.filter(sku=product_id_or_sku).first()
            if not product:
                raise ValueError(f"Product {product_id_or_sku} not found.")

        # 1. Retrieve or calculate demand forecast
        forecast = DemandForecast.objects.filter(product=product).order_by('-forecasted_at').first()
        if not forecast:
            forecast = AISlottingEngine.forecast_demand(product.id)
        demand_score = float(forecast.predicted_demand_score)

        # 2. Retrieve or calculate zone congestion risks
        zones = Zone.objects.filter(warehouse_id=warehouse_id)
        congestion_map = {}
        for z in zones:
            pred = CongestionPrediction.objects.filter(zone=z).order_by('-predicted_at').first()
            if not pred:
                # bootstrap single prediction
                pred = CongestionPrediction.objects.create(
                    zone=z,
                    congestion_risk=Decimal('0.10'),
                    predicted_traffic_volume=0
                )
            congestion_map[str(z.id)] = float(pred.congestion_risk)

        # Find closest Dock to layout center for traversal benchmark
        docks = NavigationNode.objects.filter(warehouse_id=warehouse_id, node_type__iexact='DOCK')
        dock_node = docks.first()
        if not dock_node:
            # Fallback mock/first node
            dock_node = NavigationNode.objects.filter(warehouse_id=warehouse_id).first()

        # Find all empty or available bins
        candidate_bins = Bin.objects.filter(
            is_occupied=False,
            shelf__rack__zone__warehouse_id=warehouse_id
        ).select_related('shelf', 'shelf__rack', 'shelf__rack__zone')

        scores_to_create = []
        bin_evaluations = []

        for candidate in candidate_bins:
            # SAFETY CONSTRAINT: Shelf must support the product weight
            # Rack maximum weight vs product weight
            shelf_max = float(candidate.shelf.max_weight)
            prod_weight = float(product.weight)
            if shelf_max < prod_weight:
                continue

            # Resolve coordinate proximity & route cost
            try:
                bin_node = PathfindingService.resolve_location_to_node(warehouse_id, candidate.bin_code)
            except Exception:
                # Fallback to closest matching intersection node
                bin_node = NavigationNode.objects.filter(warehouse_id=warehouse_id).first()

            # Travel Cost from nearest dock
            travel_cost = 10.0
            if dock_node and bin_node:
                try:
                    # Run A* to get dynamic cost including graph congestion
                    travel_cost, _ = PathfindingService.a_star_search(warehouse_id, dock_node, bin_node)
                except Exception:
                    # Fallback Euclidean distance
                    dx = float(dock_node.x) - float(bin_node.x)
                    dy = float(dock_node.y) - float(bin_node.y)
                    travel_cost = math.sqrt(dx*dx + dy*dy)

            # Proximity reward: Fast movers should be closer to Docks
            # Reward is higher when distance is low AND demand is high
            proximity_reward = (1.0 - min(travel_cost / 100.0, 0.95)) * demand_score * 15.0

            # Congestion Penalty
            zone_id = str(candidate.shelf.rack.zone_id)
            congestion_score = congestion_map.get(zone_id, 0.1)
            congestion_penalty = congestion_score * 5.0

            # Category Affinity Bonus
            # Look at neighbor bins in the same shelf containing same category products
            affinity_bonus = 0.0
            if product.category_id:
                # Check allocations or stock in shelf
                alloc_same_cat = Bin.objects.filter(
                    shelf=candidate.shelf,
                    allocations__product__category=product.category
                ).exists()
                if alloc_same_cat:
                    affinity_bonus = 2.0

            # Final multi-factor AI Score
            final_score = 5.0 + proximity_reward - congestion_penalty + affinity_bonus - (travel_cost * 0.1)

            eval_record = {
                "bin": candidate,
                "score": final_score,
                "congestion_penalty": congestion_penalty,
                "travel_cost": travel_cost,
                "affinity_bonus": affinity_bonus
            }
            bin_evaluations.append(eval_record)

        if not bin_evaluations:
            raise ValueError("No eligible candidate bins found that pass weight constraints.")

        # Sort candidate bins
        bin_evaluations.sort(key=lambda x: x['score'], reverse=True)
        best_match = bin_evaluations[0]

        # Log slotting scores for top candidates (up to 5)
        for val in bin_evaluations[:5]:
            SlottingScore.objects.create(
                product=product,
                bin=val['bin'],
                score=Decimal(str(round(val['score'], 4))),
                congestion_penalty=Decimal(str(round(val['congestion_penalty'], 4))),
                travel_cost=Decimal(str(round(val['travel_cost'], 4))),
                affinity_bonus=Decimal(str(round(val['affinity_bonus'], 4)))
            )

        # Log general decision
        decision = AIDecision.objects.create(
            decision_type='PLACEMENT',
            input_features={
                "product_id": str(product.id),
                "sku": product.sku,
                "weight": float(product.weight),
                "demand_score": demand_score
            },
            decision_output={
                "recommended_bin_id": str(best_match['bin'].id),
                "recommended_bin_code": best_match['bin'].bin_code,
                "score": float(best_match['score']),
                "reasoning": f"Fast-moving item proximity optimization. Score: {round(best_match['score'], 2)}"
            }
        )

        # Create active Recommendation
        rec = AllocationRecommendation.objects.create(
            product=product,
            recommended_bin=best_match['bin'],
            confidence_score=Decimal('0.92'),
            reasoning={
                "logic": f"AI optimized location. Proximity reward: +{round(best_match['score'] - 5, 2)}. Avoided bottlenecks."
            }
        )

        # Broadcast WebSockets event to recommendations channel
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "recommendation_updates",
                    {
                        "type": "recommendation_message",
                        "event": "new_recommendation",
                        "data": {
                            "recommendation_id": str(rec.id),
                            "product_sku": product.sku,
                            "bin_code": best_match['bin'].bin_code,
                            "confidence_score": 0.92,
                            "reasoning": rec.reasoning["logic"]
                        }
                    }
                )
        except Exception:
            pass

        return rec
