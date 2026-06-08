import pytest
from rest_framework import status
from django.urls import reverse
from apps.warehouse.infrastructure.persistence.models import Warehouse, WarehouseLayout, Rack, SpatialEntity, WarehousePath, NavigationNode
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary
from apps.warehouse.infrastructure.persistence.models import Shelf, Bin
from apps.identity.infrastructure.persistence.models import User

@pytest.mark.django_db
class TestTwinAPI:
    def test_digital_twin_endpoints(self, client):
        # Create tester user & obtain JWT token
        user = User.objects.create_user(
            username='twin_tester',
            password='testpassword123',
            email='twin_tester@example.com'
        )
        login_url = reverse('token_obtain_pair')
        login_res = client.post(login_url, {'username': 'twin_tester', 'password': 'testpassword123'}, content_type='application/json')
        assert login_res.status_code == status.HTTP_200_OK
        access_token = login_res.data['access']
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

        # Create standard Warehouse structures
        warehouse = Warehouse.objects.create(name='Twin Test Warehouse')
        layout = WarehouseLayout.objects.create(
            warehouse=warehouse,
            layout_name='Twin Layout v1',
            width=200.0,
            height=200.0,
            depth=50.0
        )
        zone = Zone.objects.create(
            warehouse=warehouse,
            zone_name='East Picking Zone',
            zone_type='DRY',
            x=10, y=10, z=0, width=50, height=50, depth=10
        )
        ZoneBoundary.objects.create(
            zone=zone,
            polygon_points=[{'x': 10, 'y': 10}, {'x': 60, 'y': 10}, {'x': 60, 'y': 60}]
        )
        rack = Rack.objects.create(
            zone=zone,
            rack_code='TWIN-RACK-01',
            max_weight=1000.0,
            x=15, y=15, z=0, width=4, height=8, depth=2, rotation_angle=0.0
        )
        shelf = Shelf.objects.create(
            rack=rack,
            shelf_number=1,
            max_weight=500.0,
            height_from_ground=0.0
        )
        bin1 = Bin.objects.create(
            shelf=shelf,
            bin_code='TWIN-B01',
            max_capacity=50.0,
            current_capacity=10.0,
            is_occupied=True
        )
        bin2 = Bin.objects.create(
            shelf=shelf,
            bin_code='TWIN-B02',
            max_capacity=50.0,
            current_capacity=0.0,
            is_occupied=False
        )

        # Setup Path network
        path_entity = WarehousePath.objects.create(
            warehouse=warehouse,
            path_name='Corridor East',
            start_x=10.0, start_y=0.0, start_z=0.0,
            end_x=10.0, end_y=100.0, end_z=0.0,
            width=3.0, is_two_way=True
        )
        node = NavigationNode.objects.create(
            warehouse=warehouse,
            node_name='Node-East-1',
            node_type='PICK_POINT',
            x=10.0, y=50.0, z=0.0,
            connections=[]
        )

        # Setup general spatial obstacle
        obstacle = SpatialEntity.objects.create(
            warehouse=warehouse,
            entity_name='Safety Pole 1',
            entity_type='OBSTACLE',
            x=30.0, y=30.0, z=0.0,
            width=1.0, height=4.0, depth=1.0
        )

        # 1. Test GET /api/twin/layout/<layout_id>
        res = client.get(f'/api/twin/layout/{layout.id}', **headers)
        assert res.status_code == status.HTTP_200_OK
        assert res.data['layout']['layout_name'] == 'Twin Layout v1'
        assert len(res.data['zones']) == 1
        assert len(res.data['zones'][0]['boundaries']) == 1
        assert len(res.data['racks']) == 1
        assert len(res.data['racks'][0]['shelves']) == 1
        assert len(res.data['racks'][0]['shelves'][0]['bins']) == 2
        assert len(res.data['spatial_entities']) == 1
        assert len(res.data['paths']) == 1
        assert len(res.data['navigation_nodes']) == 1

        # Helper to get the list of results whether paginated or not
        def get_results(data):
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            return data

        # 2. Test GET /api/twin/racks
        res_racks = client.get('/api/twin/racks', **headers)
        assert res_racks.status_code == status.HTTP_200_OK
        racks_list = get_results(res_racks.data)
        assert len(racks_list) == 1
        assert racks_list[0]['rack_code'] == 'TWIN-RACK-01'

        # 3. Test GET /api/twin/zones
        res_zones = client.get('/api/twin/zones', **headers)
        assert res_zones.status_code == status.HTTP_200_OK
        zones_list = get_results(res_zones.data)
        assert len(zones_list) == 1
        assert zones_list[0]['zone_name'] == 'East Picking Zone'

        # 4. Test GET /api/twin/occupancy
        res_occ = client.get('/api/twin/occupancy', **headers)
        assert res_occ.status_code == status.HTTP_200_OK
        # Overall utilization
        assert res_occ.data['overall']['total_bins'] == 2
        assert res_occ.data['overall']['occupied_bins'] == 1
        assert res_occ.data['overall']['occupancy_percentage'] == 50.0
        # Per-rack utilization
        assert len(res_occ.data['racks']) == 1
        assert res_occ.data['racks'][0]['rack_code'] == 'TWIN-RACK-01'
        assert res_occ.data['racks'][0]['occupancy_percentage'] == 50.0

        # 5. Test GET /api/twin/paths
        res_paths = client.get('/api/twin/paths', **headers)
        assert res_paths.status_code == status.HTTP_200_OK
        paths_list = get_results(res_occ.data.get('paths', res_paths.data['paths']))
        assert len(paths_list) == 1
