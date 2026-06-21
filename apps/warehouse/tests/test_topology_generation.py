import pytest
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.warehouse.infrastructure.persistence.models import (
    Warehouse, WarehouseLayout, CADObject, MLExtraction, Rack, Zone, Shelf, Bin,
    NavigationNode, NavigationEdge, StorageLocationNodeMap
)
from apps.identity.infrastructure.persistence.models import User
from apps.warehouse.application.services.dwg_conversion_service import DWGConversionService

@pytest.mark.django_db
class TestTopologyGenerationAPI:
    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        self.client = client
        self.user = User.objects.create_user(
            username='topo_tester',
            password='testpassword123',
            email='topo_tester@example.com'
        )
        login_url = reverse('token_obtain_pair')
        login_res = self.client.post(login_url, {'username': 'topo_tester', 'password': 'testpassword123'}, content_type='application/json')
        self.access_token = login_res.data['access']
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.access_token}'}

        # Build basic layout setup
        self.warehouse = Warehouse.objects.create(name='Topological Warehouse')
        self.layout = WarehouseLayout.objects.create(
            warehouse=self.warehouse,
            layout_name='Central Grid Layout',
            cad_file_url='/media/layouts/cdc_layout.dxf',
            width=Decimal('100.0'), height=Decimal('100.0'), depth=Decimal('50.0')
        )
        self.zone = Zone.objects.create(
            warehouse=self.warehouse,
            zone_name='Storage Zone 1',
            zone_type='DRY',
            x=Decimal('10.0'), y=Decimal('10.0'), z=Decimal('0.0'),
            width=Decimal('30.0'), height=Decimal('10.0'), depth=Decimal('30.0')
        )
        self.rack = Rack.objects.create(
            zone=self.zone,
            rack_code='RACK-Z1-01',
            max_weight=Decimal('1000.00'),
            x=Decimal('10.0'), y=Decimal('10.0'), z=Decimal('0.0'),
            width=Decimal('10.0'), height=Decimal('8.0'), depth=Decimal('2.0'),
            rotation_angle=Decimal('0.0')
        )

        # Create a path entity in spatial DB
        self.path_cad = CADObject.objects.create(
            layout=self.layout,
            object_type='path',
            detected_label='Aisle Pathway',
            confidence_score=0.98,
            x=Decimal('15.0'), y=Decimal('15.0'), z=Decimal('0.0'),
            width=Decimal('20.0'), height=Decimal('1.0'), depth=Decimal('1.0')
        )
        self.path_extract = MLExtraction.objects.create(
            object=self.path_cad,
            extracted_data={
                "type": "path",
                "name": "Aisle Pathway",
                "points": [{"x": 5.0, "y": 15.0}, {"x": 25.0, "y": 15.0}]
            }
        )

    def test_dwg_conversion_service_fallback(self):
        """Test that DWGConversionService returns a valid minimal fallback DXF path on missing converter tool."""
        dwg_filename = "test_warehouse.dwg"
        dxf_path = DWGConversionService.convert_dwg_to_dxf(dwg_filename)
        assert dxf_path.endswith('.dxf')
        assert dxf_path.startswith('test_warehouse')
        import os
        assert os.path.exists(dxf_path)
        # Clean up
        os.remove(dxf_path)

    def test_generate_topology_lifecycle(self):
        """Test POST /api/layout/generate-topology and subsequent layout graph retrieval."""
        generate_url = '/api/layout/generate-topology'
        payload = {
            'layout_id': str(self.layout.id),
            'shelves_per_rack': 4,
            'bins_per_shelf': 5
        }

        # 1. Trigger topology generation
        response = self.client.post(generate_url, payload, format='json', **self.headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['shelves_created'] == 4
        assert response.data['bins_created'] == 20
        assert response.data['navigation_nodes_created'] == 4  # DOCK_MAIN, 2 path nodes, 1 rack pick node

        # Verify DB insertions
        assert Shelf.objects.filter(rack=self.rack).count() == 4
        assert Bin.objects.filter(shelf__rack=self.rack).count() == 20
        assert NavigationNode.objects.filter(warehouse=self.warehouse).count() == 4
        assert NavigationEdge.objects.filter(warehouse=self.warehouse).count() == 6 # bi-directional edges (1 path seg = 2 edges, 1 pick connector = 2 edges)
        assert StorageLocationNodeMap.objects.filter(warehouse=self.warehouse).count() == 20

        # Verify Digital Twin sync initialization
        b = Bin.objects.filter(shelf__rack=self.rack).first()
        assert b.current_capacity == Decimal('0.00')

        # 2. Get Layout Graph
        graph_url = f'/api/layout/graph?layout_id={self.layout.id}'
        response_graph = self.client.get(graph_url, **self.headers)
        assert response_graph.status_code == status.HTTP_200_OK
        assert 'nodes' in response_graph.data
        assert 'edges' in response_graph.data
        assert len(response_graph.data['nodes']) == 4
        assert len(response_graph.data['edges']) == 6
