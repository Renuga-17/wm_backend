import pytest
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from apps.warehouses.models import Warehouse, WarehouseLayout, CADObject, MLExtraction, Rack, SpatialEntity
from apps.zones.models import Zone, ZoneBoundary
from apps.users.models import User
import os

@pytest.mark.django_db
class TestLayoutAPI:
    def test_layout_lifecycle_upload_and_analyze(self, client):
        # Create tester user & obtain JWT token
        user = User.objects.create_user(
            username='layout_tester',
            password='testpassword123',
            email='layout_tester@example.com'
        )
        login_url = reverse('token_obtain_pair')
        login_res = client.post(login_url, {'username': 'layout_tester', 'password': 'testpassword123'}, content_type='application/json')
        assert login_res.status_code == status.HTTP_200_OK
        access_token = login_res.data['access']
        headers = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

        # Create standard Warehouse
        warehouse = Warehouse.objects.create(name='Layout Test Warehouse')

        # 1. Test POST /api/layout/upload
        # Create a mock DXF file content
        dxf_content = b"0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nEOF"
        mock_file = SimpleUploadedFile("warehouse_floorplan.dxf", dxf_content, content_type="application/dxf")

        upload_url = '/api/layout/upload'
        payload = {
            'warehouse_id': str(warehouse.id),
            'layout_name': 'Ingestion Floorplan v1',
            'file': mock_file,
            'width': 120.00,
            'height': 120.00,
            'depth': 40.00
        }

        res_upload = client.post(upload_url, payload, format='multipart', **headers)
        assert res_upload.status_code == status.HTTP_201_CREATED
        layout_id = res_upload.data['id']
        assert res_upload.data['layout_name'] == 'Ingestion Floorplan v1'
        assert 'warehouse_floorplan' in res_upload.data['cad_file_url']

        # 2. Test GET /api/layout/:id
        detail_url = f'/api/layout/{layout_id}'
        res_detail = client.get(detail_url, **headers)
        assert res_detail.status_code == status.HTTP_200_OK
        assert res_detail.data['id'] == layout_id

        # 3. Test POST /api/layout/analyze (Mocking the external AI Service API call)
        analyze_url = '/api/layout/analyze'
        
        # We mock AIServiceClient.analyze_layout to return a clean set of AI objects (YOLO / OCR / GPT results)
        mock_ai_entities = {
            "success": True,
            "entities": [
                {
                    "type": "zone",
                    "name": "Zone A - High Velocity",
                    "x": 10.0, "y": 15.0, "z": 0.0,
                    "width": 15.0, "height": 15.0, "depth": 5.0,
                    "points": [{"x": 2.5, "y": 7.5}, {"x": 17.5, "y": 7.5}, {"x": 17.5, "y": 22.5}, {"x": 2.5, "y": 22.5}]
                },
                {
                    "type": "rack",
                    "name": "RACK-EAST-01",
                    "x": 8.0, "y": 12.0, "z": 0.0,
                    "width": 4.0, "height": 8.0, "depth": 2.0,
                    "rotation": 0.0
                },
                {
                    "type": "obstacle",
                    "name": "Safety Fire Hydrant",
                    "x": 20.0, "y": 20.0, "z": 0.0,
                    "width": 1.5, "height": 2.0, "depth": 1.5,
                    "rotation": 45.0
                }
            ]
        }

        with patch('integrations.ai_service_client.AIServiceClient.analyze_layout') as mock_analyze:
            mock_analyze.return_value = mock_ai_entities

            res_analyze = client.post(analyze_url, {'layout_id': layout_id}, content_type='application/json', **headers)
            assert res_analyze.status_code == status.HTTP_200_OK
            assert res_analyze.data['success'] is True
            assert res_analyze.data['entities_found'] == 3
            assert res_analyze.data['entities_created'] == 3

        # Verify DB insertions
        assert CADObject.objects.filter(layout_id=layout_id).count() == 3
        assert MLExtraction.objects.count() == 3
        assert Zone.objects.filter(zone_name="Zone A - High Velocity").exists() is True
        assert ZoneBoundary.objects.count() == 1
        assert Rack.objects.filter(rack_code="RACK-EAST-01").exists() is True
        assert SpatialEntity.objects.filter(entity_name="Safety Fire Hydrant").exists() is True

        # 4. Test GET /api/layout/entities
        entities_url = f'/api/layout/entities?layout_id={layout_id}'
        res_entities = client.get(entities_url, **headers)
        assert res_entities.status_code == status.HTTP_200_OK
        assert len(res_entities.data) == 3
        assert res_entities.data[0]['object_type'] in ['zone', 'rack', 'obstacle']
        assert 'dimensions' in res_entities.data[0]
        assert 'coordinates' in res_entities.data[0]
        assert 'extracted_metadata' in res_entities.data[0]
