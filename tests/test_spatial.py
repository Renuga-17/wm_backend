import pytest
from rest_framework import status
from django.urls import reverse
from apps.warehouses.models import Warehouse, Rack
from apps.zones.models import Zone
from apps.users.models import User

@pytest.mark.django_db
class TestSpatialAPI:
    def test_spatial_coordinates_endpoints(self, client):
        # Create user & login to get JWT
        user = User.objects.create_user(
            username='spatial_tester',
            password='testpassword123',
            email='tester@example.com'
        )
        login_url = reverse('token_obtain_pair')
        res = client.post(login_url, {'username': 'spatial_tester', 'password': 'testpassword123'}, content_type='application/json')
        assert res.status_code == status.HTTP_200_OK
        access_token = res.data['access']
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

        # Setup standard Warehouse
        warehouse = Warehouse.objects.create(name='Spatial Test Warehouse')

        # Setup standard Zone
        zone = Zone.objects.create(
            warehouse=warehouse,
            zone_name='Spatial Zone',
            zone_type='DRY',
            x=0, y=0, z=0, width=10, height=10, depth=10
        )

        # Setup standard Rack
        rack = Rack.objects.create(
            zone=zone,
            rack_code='SPATIAL-RACK-01',
            max_weight=500.0,
            x=1, y=2, z=0, width=2, height=2, depth=6, rotation_angle=90.0
        )

        # Helper to get the list of results whether paginated or not
        def get_results(data):
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            return data

        # 1. Test Spatial Entity Endpoint
        spatial_url = '/api/warehouses/spatial-entities/'
        payload_entity = {
            'warehouse': str(warehouse.id),
            'entity_name': 'Safety Barrier Alpha',
            'entity_type': 'OBSTACLE',
            'x': '5.0000',
            'y': '5.0000',
            'z': '0.0000',
            'width': '1.0000',
            'height': '1.0000',
            'depth': '2.0000',
            'rotation_angle': '0.0000'
        }
        res_post = client.post(spatial_url, payload_entity, content_type='application/json', **headers)
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['entity_name'] == 'Safety Barrier Alpha'

        res_get = client.get(spatial_url, **headers)
        assert res_get.status_code == status.HTTP_200_OK
        results = get_results(res_get.data)
        assert len(results) == 1
        assert results[0]['entity_type'] == 'OBSTACLE'

        # 2. Test Navigation Nodes Endpoint
        nav_url = '/api/warehouses/navigation-nodes/'
        payload_node = {
            'warehouse': str(warehouse.id),
            'node_name': 'Intersection-North-1',
            'node_type': 'INTERSECTION',
            'x': '12.5000',
            'y': '24.0000',
            'z': '0.0000',
            'connections': [{'node_id': 'another-node-id', 'weight': 5}]
        }
        res_post = client.post(nav_url, payload_node, content_type='application/json', **headers)
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['node_name'] == 'Intersection-North-1'
        assert len(res_post.data['connections']) == 1

        res_get = client.get(nav_url, **headers)
        assert res_get.status_code == status.HTTP_200_OK
        results = get_results(res_get.data)
        assert len(results) == 1

        # 3. Test Paths Endpoint
        path_url = '/api/warehouses/paths/'
        payload_path = {
            'warehouse': str(warehouse.id),
            'path_name': 'Central Corridor A',
            'start_x': '0.0000',
            'start_y': '0.0000',
            'start_z': '0.0000',
            'end_x': '50.0000',
            'end_y': '0.0000',
            'end_z': '0.0000',
            'width': '3.5000',
            'is_two_way': True
        }
        res_post = client.post(path_url, payload_path, content_type='application/json', **headers)
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['path_name'] == 'Central Corridor A'

        res_get = client.get(path_url, **headers)
        assert res_get.status_code == status.HTTP_200_OK
        results = get_results(res_get.data)
        assert len(results) == 1

        # 4. Test Zone Boundaries Endpoint
        boundary_url = '/api/zones/boundaries/'
        payload_boundary = {
            'zone': str(zone.id),
            'polygon_points': [{'x': 0, 'y': 0}, {'x': 10, 'y': 0}, {'x': 10, 'y': 10}, {'x': 0, 'y': 10}]
        }
        res_post = client.post(boundary_url, payload_boundary, content_type='application/json', **headers)
        assert res_post.status_code == status.HTTP_201_CREATED
        assert len(res_post.data['polygon_points']) == 4

        res_get = client.get(boundary_url, **headers)
        assert res_get.status_code == status.HTTP_200_OK
        results = get_results(res_get.data)
        assert len(results) == 1

        # 5. Test Rack Coordinates Access Point Endpoint
        coord_url = '/api/warehouses/rack-coordinates/'
        payload_coord = {
            'rack': str(rack.id),
            'access_point_x': '1.5000',
            'access_point_y': '2.0000',
            'access_point_z': '0.0000',
            'side': 'FRONT'
        }
        res_post = client.post(coord_url, payload_coord, content_type='application/json', **headers)
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['side'] == 'FRONT'

        res_get = client.get(coord_url, **headers)
        assert res_get.status_code == status.HTTP_200_OK
        results = get_results(res_get.data)
        assert len(results) == 1
