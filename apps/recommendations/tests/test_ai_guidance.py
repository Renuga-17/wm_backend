from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from unittest.mock import patch

from apps.warehouse.models import Warehouse, ZoneGroup, Zone, Rack, Shelf, Bin, NavigationNode
from apps.inventory.infrastructure.persistence.models import Product, ProductCategory, ProductDimension
from apps.recommendations.models.storage_recommendation import StorageRecommendation
from apps.recommendations.models.bin_allocation import BinAllocation
from apps.recommendations.services.ai_navigation_guidance_service import AINavigationGuidanceService
from apps.recommendations.services.ai_placement_guidance_service import AIPlacementGuidanceService

User = get_user_model()

class TestAIGuidance(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_guidance_user',
            password='test_guidance_password',
            email='test_guidance@warehouse.com',
            role='STAFF'
        )
        self.client.force_authenticate(user=self.user)

        self.warehouse = Warehouse.objects.create(
            name='Primary Warehouse',
            location='Aisle A',
            total_area_sqft=Decimal('5000.00')
        )

        self.zone_group = ZoneGroup.objects.create(
            warehouse=self.warehouse,
            code='A',
            name='Zone Group A',
            zone_group_type='GENERAL_STORAGE'
        )

        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_group=self.zone_group,
            zone_name='Zone A',
            zone_type='GENERAL',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            width=Decimal('10.0'), height=Decimal('10.0'), depth=Decimal('10.0')
        )

        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='Rack R1',
            max_weight=Decimal('500.00'),
            x=Decimal('1.0'), y=Decimal('1.0'), z=Decimal('0.0'),
            width=Decimal('2.0'), height=Decimal('8.0'), depth=Decimal('1.0'),
            rotation_angle=Decimal('0.0')
        )

        self.shelf = Shelf.objects.create(
            rack=self.rack,
            shelf_number=2,
            max_weight=Decimal('100.00'),
            height_from_ground=Decimal('0.5')
        )

        self.bin = Bin.objects.create(
            shelf=self.shelf,
            bin_code='Bin B4',
            max_capacity=Decimal('10.00'),
            current_capacity=Decimal('1.00'),
            length=Decimal('50.00'),
            width=Decimal('40.00'),
            height=Decimal('30.00'),
            is_occupied=False
        )

        self.category = ProductCategory.objects.create(category_name='Logistics')

        self.product = Product.objects.create(
            category=self.category,
            sku='SKU-LAPTOP-01',
            product_name='Premium Laptop',
            weight=Decimal('3.50')
        )

        self.dimension = ProductDimension.objects.create(
            product=self.product,
            length=Decimal('40.00'),
            width=Decimal('30.00'),
            height=Decimal('20.00'),
            box_length=Decimal('42.00'),
            box_width=Decimal('32.00'),
            box_height=Decimal('22.00')
        )

        self.recommendation = StorageRecommendation.objects.create(
            product=self.product,
            zone_group=self.zone_group,
            zone=self.zone,
            recommendation_reason='Optimal zone',
            recommendation_score=0.95,
            recommendation_source=StorageRecommendation.RecommendationSource.RULE_ENGINE,
            recommendation_version='v1'
        )

        # Setup standard navigation nodes for A* route testing
        self.dock_node = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='DOCK_A',
            node_type='DOCK',
            x=Decimal('0.0'), y=Decimal('0.0'), z=Decimal('0.0'),
            connections=[{'node_id': 'RACK_A1_NODE', 'weight': 10.0}]
        )
        self.rack_node = NavigationNode.objects.create(
            warehouse=self.warehouse,
            node_name='BIN_B4_NODE',  # Closest node will map to our Bin B4 code or rack
            node_type='PICK_POINT',
            x=Decimal('0.0'), y=Decimal('10.0'), z=Decimal('0.0'),
            connections=[]
        )

    def test_deterministic_navigation_guidance_generation(self):
        """Test local deterministic templates generate instructions correctly."""
        service = AINavigationGuidanceService()
        route_data = {
            "start_location": "DOCK_A",
            "distance": 10.0,
            "path": []
        }
        instructions = service.generate_instructions(
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin_obj=self.bin,
            route_data=route_data
        )

        expected = (
            "Walk straight from DOCK_A.\n\n"
            "Continue for 10.0 meters to Zone A.\n\n"
            "Proceed to Rack Rack R1.\n\n"
            "Locate Shelf 2.\n\n"
            "Place the product in Bin Bin B4."
        )
        self.assertEqual(instructions, expected)

    @patch('integrations.ai_service_client.AIServiceClient.generate_navigation_guidance')
    def test_navigation_guidance_fallback(self, mock_nav):
        """Test fallback to Gemini when route_data is corrupted."""
        mock_nav.return_value = {"instructions": "Walk down main hallway and turn right."}
        
        service = AINavigationGuidanceService()
        # Missing start_location will cause KeyError / AttributeError or generic template fail
        instructions = service.generate_instructions(
            zone=self.zone,
            rack=self.rack,
            shelf=self.shelf,
            bin_obj=self.bin,
            route_data=None  # Force template error
        )
        self.assertEqual(instructions, "Walk down main hallway and turn right.")
        mock_nav.assert_called_once()

    def test_deterministic_placement_guidance_generation(self):
        """Test local deterministic templates generate placement instructions correctly."""
        service = AIPlacementGuidanceService()
        
        # Mock a placement_3d object
        class MockPlacement3D:
            placement_strategy = 'STACKED'
            label_direction = 'TOP'
            utilization_percentage = Decimal('92.0')

        instructions = service.generate_instructions(
            product_dim=self.dimension,
            selected_orientation='40x30x20',
            placement_3d=MockPlacement3D(),
            bin_obj=self.bin
        )

        expected = (
            "Place the product stacked on top of existing inventory.\n\n"
            "Align the product to dimensions: 40x30x20.\n\n"
            "Keep the label facing upward.\n\n"
            "This orientation provides optimal space utilization of 92.0%."
        )
        self.assertEqual(instructions, expected)

    @patch('integrations.ai_service_client.AIServiceClient.generate_placement_guidance')
    def test_placement_guidance_fallback(self, mock_place):
        """Test fallback to Gemini when placement_3d is corrupted/None."""
        mock_place.return_value = {"instructions": "Place with label front-facing."}
        
        service = AIPlacementGuidanceService()
        instructions = service.generate_instructions(
            product_dim=self.dimension,
            selected_orientation='40x30x20',
            placement_3d=None,  # Force template error
            bin_obj=self.bin
        )
        self.assertEqual(instructions, "Place with label front-facing.")
        mock_place.assert_called_once()

    @patch('apps.warehouse.application.services.route_optimizer.RouteOptimizer.compute_route')
    def test_allocation_api_response_includes_guidance(self, mock_route):
        """Test the bin-allocation POST endpoint returns unified instructions."""
        mock_route.return_value = {
            "distance": 10.0,
            "path": [
                {"node": "DOCK_A", "x": 0.0, "y": 0.0, "z": 0.0},
                {"node": "BIN_B4_NODE", "x": 0.0, "y": 10.0, "z": 0.0}
            ]
        }

        url = '/api/recommendations/bin-allocation/'
        response = self.client.post(url, {'product_id': str(self.product.id)}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data

        # Verify guidance fields are present and correctly templated
        self.assertIn("navigation_instructions", data)
        self.assertIn("placement_instructions", data)
        self.assertIn("placement_3d", data)
        self.assertIn("route", data)

        self.assertIn("Walk straight from DOCK_A", data["navigation_instructions"])
        self.assertIn("Place the product horizontally", data["placement_instructions"])
        
        self.assertEqual(data["route"]["distance"], 10.0)
        self.assertEqual(data["route"]["path"], [[0.0, 0.0], [0.0, 10.0]])
        # volume math: product_vol / bin_vol. Here: product = 40*30*20 = 24,000. Bin = 50*40*30 = 60,000.
        # Utilization = (24,000/60,000) * 100 = 40.0%
        self.assertEqual(float(data["placement_3d"]["utilization_percentage"]), 40.0)
