import math
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.exceptions import ValidationError
from apps.products.models import Product
from apps.bins.models import Bin
from apps.zones.models import Zone
from apps.movements.models import StockMovement
from apps.warehouses.models import NavigationNode, NavigationEdge, Rack
from apps.recommendations.models import DemandForecast, CongestionPrediction, SlottingScore, AIDecision, AllocationRecommendation
from apps.routes.services.pathfinding import PathfindingService
from apps.recommendations.ai_engine.feedback_loop import AIFeedbackLoop

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
        except (Product.DoesNotExist, ValueError, ValidationError):
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
    def calculate_all_slotting_scores(product_id_or_sku, warehouse_id):
        """
        Calculates detail metrics and multi-factor scores for all candidate bins in a warehouse.
        """
        try:
            product = Product.objects.get(id=product_id_or_sku)
        except (Product.DoesNotExist, ValueError, ValidationError):
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

        # Pre-compute travel costs from the nearest dock to all other nodes once using Dijkstra's algorithm.
        travel_costs = {}
        if dock_node:
            try:
                import heapq
                nodes_map, graph = PathfindingService.get_graph(warehouse_id)
                dock_id = str(dock_node.id)
                
                queue = [(0.0, dock_id)]
                travel_costs = {nid: float('inf') for nid in nodes_map}
                travel_costs[dock_id] = 0.0
                
                while queue:
                    current_dist, current_id = heapq.heappop(queue)
                    if current_dist > travel_costs[current_id]:
                        continue
                    for neighbor_id, cost in graph.get(current_id, []):
                        dist = current_dist + cost
                        if dist < travel_costs[neighbor_id]:
                            travel_costs[neighbor_id] = dist
                            heapq.heappush(queue, (dist, neighbor_id))
            except Exception:
                pass

        # Pre-fetch all navigation nodes to avoid N+1 query bottleneck inside the loop
        nodes_by_name = {n.node_name: n for n in NavigationNode.objects.filter(warehouse_id=warehouse_id)}
        fallback_node = NavigationNode.objects.filter(warehouse_id=warehouse_id).first()

        # Pre-fetch all shelf IDs containing same category to avoid N+1 queries inside loop
        shelves_with_same_cat = set()
        if product.category_id:
            try:
                shelves_with_same_cat = set(
                    Bin.objects.filter(
                        allocations__product__category=product.category
                    ).values_list('shelf_id', flat=True)
                )
            except Exception:
                pass

        # Get dynamic weights from AIFeedbackLoop
        weights = AIFeedbackLoop.get_current_weights()

        # Find all empty or available bins
        candidate_bins = Bin.objects.filter(
            is_occupied=False,
            shelf__rack__zone__warehouse_id=warehouse_id
        ).select_related('shelf', 'shelf__rack', 'shelf__rack__zone')

        bin_evaluations = []
        for candidate in candidate_bins:
            # SAFETY CONSTRAINT: Shelf must support the product weight
            shelf_max = float(candidate.shelf.max_weight)
            prod_weight = float(product.weight)
            if shelf_max < prod_weight:
                continue

            # Resolve coordinate proximity & route cost using pre-fetched nodes
            bin_node = nodes_by_name.get(candidate.bin_code, fallback_node)

            # Travel Cost from nearest dock
            travel_cost = 10.0
            if dock_node and bin_node:
                travel_cost = travel_costs.get(str(bin_node.id), float('inf'))
                if travel_cost == float('inf'):
                    # Fallback Euclidean distance
                    dx = float(dock_node.x) - float(bin_node.x)
                    dy = float(dock_node.y) - float(bin_node.y)
                    travel_cost = math.sqrt(dx*dx + dy*dy)

            # Proximity reward: Fast movers should be closer to Docks
            proximity_reward = (1.0 - min(travel_cost / 100.0, 0.95)) * demand_score * weights.get('proximity_reward_factor', 15.0)

            # Congestion Penalty
            zone_id = str(candidate.shelf.rack.zone_id)
            congestion_score = congestion_map.get(zone_id, 0.1)
            congestion_penalty = congestion_score * weights.get('congestion_penalty_factor', 5.0)

            # Category Affinity Bonus using pre-fetched shelves
            affinity_bonus = 0.0
            if candidate.shelf_id in shelves_with_same_cat:
                affinity_bonus = weights.get('affinity_bonus_factor', 2.0)

            # Final multi-factor AI Score
            final_score = 5.0 + proximity_reward - congestion_penalty + affinity_bonus - (travel_cost * weights.get('travel_cost_factor', 0.1))

            bin_evaluations.append({
                "bin": candidate,
                "bin_code": candidate.bin_code,
                "zone_name": candidate.shelf.rack.zone.zone_name,
                "score": round(final_score, 4),
                "proximity_reward": round(proximity_reward, 4),
                "congestion_penalty": round(congestion_penalty, 4),
                "travel_cost": round(travel_cost, 4),
                "affinity_bonus": round(affinity_bonus, 4)
            })

        bin_evaluations.sort(key=lambda x: x['score'], reverse=True)
        return bin_evaluations

    @staticmethod
    def optimize_slotting(product_id_or_sku, warehouse_id):
        """
        Determines the operationally optimal bin placement using predictive multi-factor score.
        Considers structural safety, demand proximity, congestion penalty, category affinity, and route cost.
        """
        try:
            product = Product.objects.get(id=product_id_or_sku)
        except (Product.DoesNotExist, ValueError, ValidationError):
            product = Product.objects.filter(sku=product_id_or_sku).first()
            if not product:
                raise ValueError(f"Product {product_id_or_sku} not found.")

        # 1. Retrieve or calculate demand forecast
        forecast = DemandForecast.objects.filter(product=product).order_by('-forecasted_at').first()
        if not forecast:
            forecast = AISlottingEngine.forecast_demand(product.id)
        demand_score = float(forecast.predicted_demand_score)

        # Calculate scores for all candidate bins
        bin_evaluations = AISlottingEngine.calculate_all_slotting_scores(product.id, warehouse_id)
        if not bin_evaluations:
            raise ValueError("No eligible candidate bins found that pass weight constraints.")

        best_match = bin_evaluations[0]

        # Log slotting scores for top candidates (up to 5)
        for val in bin_evaluations[:5]:
            SlottingScore.objects.create(
                product=product,
                bin=val['bin'],
                score=Decimal(str(val['score'])),
                congestion_penalty=Decimal(str(val['congestion_penalty'])),
                travel_cost=Decimal(str(val['travel_cost'])),
                affinity_bonus=Decimal(str(val['affinity_bonus']))
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
                "recommended_bin_code": best_match['bin_code'],
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
                "logic": f"AI optimized location. Proximity reward: +{round(best_match['proximity_reward'], 2)}. Avoided bottlenecks."
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
                            "bin_code": best_match['bin_code'],
                            "confidence_score": 0.92,
                            "reasoning": rec.reasoning["logic"]
                        }
                    }
                )
                # Broadcast alert to Slotting WS group
                async_to_sync(channel_layer.group_send)(
                    "slotting_alerts",
                    {
                        "type": "slotting_message",
                        "event": "new_slotting_score",
                        "data": {
                            "sku": product.sku,
                            "recommended_bin": best_match['bin_code'],
                            "score": best_match['score'],
                            "reasoning": rec.reasoning["logic"]
                        }
                    }
                )
        except Exception:
            pass

        return rec
