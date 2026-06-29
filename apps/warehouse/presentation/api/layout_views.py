import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.warehouse.infrastructure.persistence.models import Warehouse, WarehouseLayout, CADObject, MLExtraction, Rack, SpatialEntity, RackCoordinate
from apps.warehouse.infrastructure.persistence.models import Zone, ZoneBoundary
from .layout_serializers import WarehouseLayoutSerializer, LayoutUploadSerializer, LayoutAnalysisSerializer
from apps.warehouse.application.services.layout_parser import LayoutParser
from integrations.ai_service_client import AIServiceClient
from common.permissions import ReadOnlyOrAuthenticated
import logging

logger = logging.getLogger(__name__)

class LayoutUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LayoutUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        warehouse = serializer.validated_data['warehouse']
        layout_name = serializer.validated_data['layout_name']
        uploaded_file = serializer.validated_data['file']
        width = serializer.validated_data['width']
        height = serializer.validated_data['height']
        depth = serializer.validated_data['depth']

        # Ensure upload folder exists
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        layout_dir = os.path.join(media_root, 'layouts')
        os.makedirs(layout_dir, exist_ok=True)

        # Save file locally
        fs = FileSystemStorage(location=layout_dir)
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = f"/media/layouts/{filename}"

        # Create Layout Record
        layout = WarehouseLayout.objects.create(
            warehouse=warehouse,
            layout_name=layout_name,
            cad_file_url=file_url,
            width=width,
            height=height,
            depth=depth
        )

        return Response(WarehouseLayoutSerializer(layout).data, status=status.HTTP_201_CREATED)


class LayoutDetailView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request, layout_id):
        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
            return Response(WarehouseLayoutSerializer(layout).data, status=status.HTTP_200_OK)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)


class LayoutAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LayoutAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        layout_id = serializer.validated_data['layout_id']
        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)

        # Resolve local file path
        # In case cad_file_url is stored as relative or absolute
        cad_url = layout.cad_file_url
        if cad_url.startswith('/media/'):
            # Convert url to local filesystem path
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            file_path = os.path.join(settings.BASE_DIR, cad_url.lstrip('/'))
            if not os.path.exists(file_path):
                # Fallback to MEDIA_ROOT
                file_path = os.path.join(media_root, 'layouts', os.path.basename(cad_url))
        else:
            file_path = cad_url

        # Detect extension
        _, ext = os.path.splitext(cad_url.lower())
        
        # 1. Parse geometries
        entities = []
        if ext == '.dwg':
            try:
                from apps.warehouse.application.services.dwg_conversion_service import DWGConversionService
                dxf_path = DWGConversionService.convert_dwg_to_dxf(file_path)
                entities = LayoutParser.parse_dxf(dxf_path)
            except Exception as dwg_err:
                logger.error(f"DWG conversion failed: {dwg_err}")
                entities = LayoutParser.parse_dxf(file_path)
        elif ext == '.dxf':
            entities = LayoutParser.parse_dxf(file_path)
        
        # 2. Call external AI Service Client for Vision / YOLO / OCR enhancement
        ai_client = AIServiceClient()
        ai_response = ai_client.analyze_layout(file_path, ext.lstrip('.'))
        
        # Merge external AI entities if they were fetched successfully
        if ai_response.get('success') and ai_response.get('entities'):
            # Clear local entities and use AI model details, or combine them
            entities = ai_response.get('entities')

        created_entities_count = 0
        extracted_objects = []

        # 3. Automatically populate the spatial database
        for ent in entities:
            # Create a CADObject record
            cad_obj = CADObject.objects.create(
                layout=layout,
                object_type=ent['type'],
                detected_label=ent['name'],
                confidence_score=ent.get('confidence', 0.95),
                x=ent['x'],
                y=ent['y'],
                z=ent['z'],
                width=ent['width'],
                height=ent['height'],
                depth=ent['depth']
            )

            # Create an associated MLExtraction record
            MLExtraction.objects.create(
                object=cad_obj,
                extracted_data=ent,
                model_version=ent.get('model_version', 'Layout-AI-v1.0')
            )

            # Convert to actual physical spatial entity
            if ent['type'] == 'zone':
                # Create a Zone
                zone = Zone.objects.create(
                    warehouse=layout.warehouse,
                    zone_name=ent['name'],
                    zone_type='DRY', # Default representation
                    x=ent['x'], y=ent['y'], z=ent['z'],
                    width=ent['width'], height=ent['height'], depth=ent['depth']
                )
                # Create Zone Boundary
                if ent.get('points'):
                    ZoneBoundary.objects.create(
                        zone=zone,
                        polygon_points=ent['points']
                    )
                created_entities_count += 1

            elif ent['type'] == 'rack':
                # Find/create a default zone to place the rack
                zone = Zone.objects.filter(warehouse=layout.warehouse).first()
                if not zone:
                    zone = Zone.objects.create(
                        warehouse=layout.warehouse,
                        zone_name='Default Zone',
                        zone_type='DRY',
                        x=0, y=0, z=0, width=50, height=50, depth=50
                    )
                # Create Rack
                rack = Rack.objects.create(
                    zone=zone,
                    rack_code=ent['name'],
                    max_weight=1000.0,
                    x=ent['x'], y=ent['y'], z=ent['z'],
                    width=ent['width'], height=ent['height'], depth=ent['depth'],
                    rotation_angle=ent.get('rotation', 0.0)
                )
                # Create RackCoordinate access point (offset relative to centroid)
                RackCoordinate.objects.create(
                    rack=rack,
                    access_point_x=ent['x'] + 1.0,
                    access_point_y=ent['y'] + 1.0,
                    access_point_z=ent['z'],
                    side='FRONT'
                )
                created_entities_count += 1

            elif ent['type'] == 'obstacle':
                # Create general SpatialEntity
                SpatialEntity.objects.create(
                    warehouse=layout.warehouse,
                    entity_name=ent['name'],
                    entity_type='OBSTACLE',
                    x=ent['x'], y=ent['y'], z=ent['z'],
                    width=ent['width'], height=ent['height'], depth=ent['depth'],
                    rotation_angle=ent.get('rotation', 0.0)
                )
                created_entities_count += 1

            extracted_objects.append({
                "id": str(cad_obj.id),
                "type": ent['type'],
                "name": ent['name'],
                "coordinates": [float(ent['x']), float(ent['y']), float(ent['z'])]
            })

        return Response({
            "success": True,
            "layout_id": str(layout.id),
            "entities_found": len(entities),
            "entities_created": created_entities_count,
            "extracted_objects": extracted_objects
        }, status=status.HTTP_200_OK)


class LayoutEntitiesView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        layout_id = request.query_params.get('layout_id')
        if not layout_id:
            return Response({"error": "layout_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve CADObjects with prefetched ml extractions to prevent N+1 query loop
        cad_objects = CADObject.objects.filter(layout_id=layout_id).prefetch_related('ml_extractions')
        
        results = []
        for obj in cad_objects:
            # Retrieve latest ml extraction from prefetch cache
            extractions = list(obj.ml_extractions.all())
            extractions.sort(key=lambda x: x.processed_at, reverse=True)
            extraction = extractions[0] if extractions else None
            
            results.append({
                "object_id": str(obj.id),
                "object_type": obj.object_type,
                "detected_label": obj.detected_label,
                "confidence_score": float(obj.confidence_score),
                "dimensions": {
                    "width": float(obj.width),
                    "height": float(obj.height),
                    "depth": float(obj.depth)
                },
                "coordinates": {
                    "x": float(obj.x),
                    "y": float(obj.y),
                    "z": float(obj.z)
                },
                "extracted_metadata": extraction.extracted_data if extraction else None
            })

        return Response(results, status=status.HTTP_200_OK)


class GenerateTopologyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .layout_serializers import GenerateTopologySerializer
        from apps.warehouse.application.services.topology_generation_service import TopologyGenerationService
        from apps.warehouse.application.services.navigation_graph_generator_service import NavigationGraphGeneratorService
        from apps.warehouse.application.services.digital_twin_sync_service import DigitalTwinSyncService
        from apps.warehouse.models import Bin
        
        serializer = GenerateTopologySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        layout_id = serializer.validated_data['layout_id']
        shelves_per_rack = serializer.validated_data['shelves_per_rack']
        bins_per_shelf = serializer.validated_data['bins_per_shelf']

        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)

        warehouse = layout.warehouse
        racks = Rack.objects.filter(zone__warehouse=warehouse)
        
        shelves_created = 0
        bins_created = 0

        # 1. Generate shelves and bins for all racks
        for rack in racks:
            sh, bn = TopologyGenerationService.generate_rack_topology(
                rack, 
                shelves_per_rack=shelves_per_rack, 
                bins_per_shelf=bins_per_shelf
            )
            shelves_created += len(sh)
            bins_created += len(bn)

        # 2. Fetch path CADObjects to build navigation graph
        path_objects = CADObject.objects.filter(layout=layout, object_type='path')
        path_entities = []
        for obj in path_objects:
            extraction = MLExtraction.objects.filter(object=obj).first()
            if extraction and isinstance(extraction.extracted_data, dict):
                path_entities.append(extraction.extracted_data)

        # 3. Generate navigation nodes, edges, and mappings
        nodes = NavigationGraphGeneratorService.generate_navigation_graph(warehouse, path_entities)

        # 4. Initialize Digital Twin
        all_bins = Bin.objects.filter(shelf__rack__zone__warehouse=warehouse)
        from decimal import Decimal
        for b in all_bins:
            DigitalTwinSyncService.sync_occupancy(
                bin_id=b.id,
                is_occupied=False,
                current_capacity=Decimal('0.00')
            )

        return Response({
            "success": True,
            "layout_id": str(layout.id),
            "warehouse_id": str(warehouse.id),
            "racks_processed": racks.count(),
            "shelves_created": shelves_created,
            "bins_created": bins_created,
            "navigation_nodes_created": len(nodes)
        }, status=status.HTTP_200_OK)


class LayoutGraphView(APIView):
    permission_classes = [ReadOnlyOrAuthenticated]

    def get(self, request):
        layout_id = request.query_params.get('layout_id')
        if not layout_id:
            return Response({"error": "layout_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = WarehouseLayout.objects.get(id=layout_id)
        except WarehouseLayout.DoesNotExist:
            return Response({"error": "Warehouse layout not found"}, status=status.HTTP_404_NOT_FOUND)

        from apps.warehouse.models import NavigationNode, NavigationEdge
        warehouse = layout.warehouse
        nodes = NavigationNode.objects.filter(warehouse=warehouse)
        edges = NavigationEdge.objects.filter(warehouse=warehouse)

        nodes_data = [
            {
                "node_id": str(n.id),
                "node_name": n.node_name,
                "node_type": n.node_type,
                "coordinates": [float(n.x), float(n.y), float(n.z)]
            }
            for n in nodes
        ]

        edges_data = [
            {
                "edge_id": str(e.id),
                "from_node_id": str(e.from_node_id),
                "to_node_id": str(e.to_node_id),
                "weight": float(e.edge_weight),
                "congestion_score": float(e.congestion_score),
                "is_blocked": e.is_blocked
            }
            for e in edges
        ]

        return Response({
            "nodes": nodes_data,
            "edges": edges_data
        }, status=status.HTTP_200_OK)
