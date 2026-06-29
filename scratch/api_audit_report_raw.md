# API & Frontend Readiness Audit

## API Details

### /api/users/login/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: No
* **Swagger/OpenAPI**: No
* **View**: TokenObtainPairView

### /api/users/token/refresh/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: No
* **Swagger/OpenAPI**: No
* **View**: TokenRefreshView

### /api/users/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: UserViewSet

### /api/users/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: UserViewSet

### /api/users/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: UserViewSet

### /api/users/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: UserViewSet

### /api/audit-logs/^scan-logs/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ScanLogViewSet

### /api/audit-logs/^scan-logs\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ScanLogViewSet

### /api/audit-logs/^scan-logs/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ScanLogViewSet

### /api/audit-logs/^scan-logs/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ScanLogViewSet

### /api/audit-logs/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AuditLogViewSet

### /api/audit-logs/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AuditLogViewSet

### /api/audit-logs/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AuditLogViewSet

### /api/audit-logs/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AuditLogViewSet

### /api/layout/upload
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: LayoutUploadView

### /api/layout/analyze
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: LayoutAnalyzeView

### /api/layout/entities
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: LayoutEntitiesView

### /api/layout/generate-topology
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: GenerateTopologyView

### /api/layout/graph
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: LayoutGraphView

### /api/layout/<uuid:layout_id>
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: LayoutDetailView

### /api/twin/layout/<uuid:layout_id>
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehouseTwinDetailView

### /api/twin/racks
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: TwinRacksView

### /api/twin/zones
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: TwinZonesView

### /api/twin/occupancy
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: TwinOccupancyView

### /api/twin/paths
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: TwinPathsView

### /api/twin/summary
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: TwinSummaryView

### /api/warehouses/^racks/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackViewSet

### /api/warehouses/^racks\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackViewSet

### /api/warehouses/^racks/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackViewSet

### /api/warehouses/^racks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackViewSet

### /api/warehouses/^spatial-entities/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: SpatialEntityViewSet

### /api/warehouses/^spatial-entities\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: SpatialEntityViewSet

### /api/warehouses/^spatial-entities/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: SpatialEntityViewSet

### /api/warehouses/^spatial-entities/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: SpatialEntityViewSet

### /api/warehouses/^navigation-nodes/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: NavigationNodeViewSet

### /api/warehouses/^navigation-nodes\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: NavigationNodeViewSet

### /api/warehouses/^navigation-nodes/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: NavigationNodeViewSet

### /api/warehouses/^navigation-nodes/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: NavigationNodeViewSet

### /api/warehouses/^paths/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehousePathViewSet

### /api/warehouses/^paths\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehousePathViewSet

### /api/warehouses/^paths/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehousePathViewSet

### /api/warehouses/^paths/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehousePathViewSet

### /api/warehouses/^rack-coordinates/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackCoordinateViewSet

### /api/warehouses/^rack-coordinates\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackCoordinateViewSet

### /api/warehouses/^rack-coordinates/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackCoordinateViewSet

### /api/warehouses/^rack-coordinates/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RackCoordinateViewSet

### /api/warehouses/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehouseViewSet

### /api/warehouses/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehouseViewSet

### /api/warehouses/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehouseViewSet

### /api/warehouses/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: WarehouseViewSet

### /api/zones/^zone-groups/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneGroupViewSet

### /api/zones/^zone-groups\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneGroupViewSet

### /api/zones/^zone-groups/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneGroupViewSet

### /api/zones/^zone-groups/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneGroupViewSet

### /api/zones/^aisles/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AisleViewSet

### /api/zones/^aisles\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AisleViewSet

### /api/zones/^aisles/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AisleViewSet

### /api/zones/^aisles/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AisleViewSet

### /api/zones/^boundaries/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneBoundaryViewSet

### /api/zones/^boundaries\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneBoundaryViewSet

### /api/zones/^boundaries/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneBoundaryViewSet

### /api/zones/^boundaries/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneBoundaryViewSet

### /api/zones/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneViewSet

### /api/zones/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneViewSet

### /api/zones/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneViewSet

### /api/zones/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ZoneViewSet

### /api/bins/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinViewSet

### /api/bins/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinViewSet

### /api/bins/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinViewSet

### /api/bins/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinViewSet

### /api/routes/generate/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: GenerateRouteView

### /api/routes/^block-path/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^block-path\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^congestion/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^congestion\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^multi-pick/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^multi-pick\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^optimize/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^optimize\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^recalculate/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^recalculate\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^(?P<pk>[^/.]+)/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/routes/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteViewSet

### /api/products/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductViewSet

### /api/products/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductViewSet

### /api/products/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductViewSet

### /api/products/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductViewSet

### /api/inventory/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^adjust/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^adjust\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^audit/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^audit\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^relocate/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^relocate\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^report-damage/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^report-damage\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^transfer/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^transfer\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/inventory/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InventoryViewSet

### /api/movements/^allocations/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: StorageAllocationViewSet

### /api/movements/^allocations\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: StorageAllocationViewSet

### /api/movements/^allocations/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: StorageAllocationViewSet

### /api/movements/^allocations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: StorageAllocationViewSet

### /api/movements/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: MovementViewSet

### /api/movements/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: MovementViewSet

### /api/movements/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: MovementViewSet

### /api/movements/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: MovementViewSet

### /api/recommendations/storage/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: StorageRecommendationView

### /api/recommendations/bin-allocation/<int:pk>/complete/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinAllocationCompleteView

### /api/recommendations/bin-allocation/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: BinAllocationView

### /api/recommendations/3d-placement/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ThreeDPlacementView

### /api/recommendations/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^allocate/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^allocate\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^suggest-bin/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^suggest-bin\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/recommendations/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RecommendationViewSet

### /api/ai/query/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RAGQueryView

### /api/ai/rag-health/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Missing
* **Serializer**: No
* **Auth/Perms**: No
* **Swagger/OpenAPI**: No
* **View**: RAGHealthView

### /api/ai/^alerts/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^alerts\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^congestion-risk/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^congestion-risk\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^feedback/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^feedback\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^hotspot-prevention/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^hotspot-prevention\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^operational-scores/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^operational-scores\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^optimize-slotting/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^optimize-slotting\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^predict-demand/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^predict-demand\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^recommendations/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^recommendations\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^slotting-score/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/ai/^slotting-score\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AIRecommendationViewSet

### /api/dashboards/^analytics/bin-heatmap/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/bin-heatmap\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/heatmaps/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/heatmaps\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/inbound-metrics/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/inbound-metrics\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/inventory-movements/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/inventory-movements\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/occupancy-trends/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/occupancy-trends\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/outbound-metrics/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/outbound-metrics\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/rack-heatmap/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/rack-heatmap\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/recommendation-metrics/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/recommendation-metrics\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/route-metrics/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/route-metrics\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/routes/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/routes\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/telemetry/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/telemetry\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/throughput/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/throughput\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/top-zones/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/top-zones\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/warehouse-kpis/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/warehouse-kpis\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/zone-heatmap/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^analytics/zone-heatmap\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: AnalyticsViewSet

### /api/dashboards/^robot-tasks/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RobotTaskViewSet

### /api/dashboards/^robot-tasks\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RobotTaskViewSet

### /api/dashboards/^robot-tasks/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RobotTaskViewSet

### /api/dashboards/^robot-tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RobotTaskViewSet

### /api/dashboards/^route-optimizations/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteOptimizationViewSet

### /api/dashboards/^route-optimizations\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteOptimizationViewSet

### /api/dashboards/^route-optimizations/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteOptimizationViewSet

### /api/dashboards/^route-optimizations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: RouteOptimizationViewSet

### /api/dashboards/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: DashboardViewSet

### /api/dashboards/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: DashboardViewSet

### /api/dashboards/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: DashboardViewSet

### /api/dashboards/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: DashboardViewSet

### /api/orders/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^assign-picker/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^assign-picker\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^close/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^close\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^dispatch/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^dispatch\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^generate-picklist/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^generate-picklist\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^optimize-route/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^optimize-route\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^pack/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^pack\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/orders/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OrderViewSet

### /api/product-classifications/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductClassificationViewSet

### /api/product-classifications/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductClassificationViewSet

### /api/product-classifications/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductClassificationViewSet

### /api/product-classifications/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductClassificationViewSet

### /api/product-dimensions/^storage-rules/$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductStorageRuleViewSet

### /api/product-dimensions/^storage-rules\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductStorageRuleViewSet

### /api/product-dimensions/^storage-rules/(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductStorageRuleViewSet

### /api/product-dimensions/^storage-rules/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductStorageRuleViewSet

### /api/product-dimensions/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductDimensionViewSet

### /api/product-dimensions/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductDimensionViewSet

### /api/product-dimensions/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductDimensionViewSet

### /api/product-dimensions/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: ProductDimensionViewSet

### /api/inbound/^$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InboundViewSet

### /api/inbound/^\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InboundViewSet

### /api/inbound/^(?P<pk>[^/.]+)/$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InboundViewSet

### /api/inbound/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET, PUT, PATCH, DELETE
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: InboundViewSet

### /api/ocr/upload/
* **Method**: GET, POST, PUT, PATCH, DELETE, HEAD, TRACE
* **Status**: Partial
* **Serializer**: No
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRUploadView

### /api/ocr/review-queue/
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/review-queue/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/review-queue\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
* **Method**: GET
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/approve/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/approve\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/reject/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/reject\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/sync-rag/$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

### /api/ocr/^documents/(?P<pk>[^/.]+)/sync-rag\.(?P<format>[a-z0-9]+)/?$
* **Method**: POST
* **Status**: Partial
* **Serializer**: Yes
* **Auth/Perms**: Yes
* **Swagger/OpenAPI**: No
* **View**: OCRDocumentViewSet

## Summary Metrics

1. **Total API Count**: 229
2. **Complete Endpoints**: 0
3. **Partial Endpoints**: 228
4. **Missing Endpoints**: 1

5. **Frontend Ready APIs**:
   * /api/users/^$
   * /api/users/^\.(?P<format>[a-z0-9]+)/?$
   * /api/users/^(?P<pk>[^/.]+)/$
   * /api/users/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/audit-logs/^scan-logs/$
   * /api/audit-logs/^scan-logs\.(?P<format>[a-z0-9]+)/?$
   * /api/audit-logs/^scan-logs/(?P<pk>[^/.]+)/$
   * /api/audit-logs/^scan-logs/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/audit-logs/^$
   * /api/audit-logs/^\.(?P<format>[a-z0-9]+)/?$
   * /api/audit-logs/^(?P<pk>[^/.]+)/$
   * /api/audit-logs/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^racks/$
   * /api/warehouses/^racks\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^racks/(?P<pk>[^/.]+)/$
   * /api/warehouses/^racks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^spatial-entities/$
   * /api/warehouses/^spatial-entities\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^spatial-entities/(?P<pk>[^/.]+)/$
   * /api/warehouses/^spatial-entities/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^navigation-nodes/$
   * /api/warehouses/^navigation-nodes\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^navigation-nodes/(?P<pk>[^/.]+)/$
   * /api/warehouses/^navigation-nodes/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^paths/$
   * /api/warehouses/^paths\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^paths/(?P<pk>[^/.]+)/$
   * /api/warehouses/^paths/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^rack-coordinates/$
   * /api/warehouses/^rack-coordinates\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^rack-coordinates/(?P<pk>[^/.]+)/$
   * /api/warehouses/^rack-coordinates/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^$
   * /api/warehouses/^\.(?P<format>[a-z0-9]+)/?$
   * /api/warehouses/^(?P<pk>[^/.]+)/$
   * /api/warehouses/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^zone-groups/$
   * /api/zones/^zone-groups\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^zone-groups/(?P<pk>[^/.]+)/$
   * /api/zones/^zone-groups/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^aisles/$
   * /api/zones/^aisles\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^aisles/(?P<pk>[^/.]+)/$
   * /api/zones/^aisles/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^boundaries/$
   * /api/zones/^boundaries\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^boundaries/(?P<pk>[^/.]+)/$
   * /api/zones/^boundaries/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^$
   * /api/zones/^\.(?P<format>[a-z0-9]+)/?$
   * /api/zones/^(?P<pk>[^/.]+)/$
   * /api/zones/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/bins/^$
   * /api/bins/^\.(?P<format>[a-z0-9]+)/?$
   * /api/bins/^(?P<pk>[^/.]+)/$
   * /api/bins/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^block-path/$
   * /api/routes/^block-path\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^congestion/$
   * /api/routes/^congestion\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^multi-pick/$
   * /api/routes/^multi-pick\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^optimize/$
   * /api/routes/^optimize\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^recalculate/$
   * /api/routes/^recalculate\.(?P<format>[a-z0-9]+)/?$
   * /api/routes/^(?P<pk>[^/.]+)/$
   * /api/routes/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/products/^$
   * /api/products/^\.(?P<format>[a-z0-9]+)/?$
   * /api/products/^(?P<pk>[^/.]+)/$
   * /api/products/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^$
   * /api/inventory/^\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^adjust/$
   * /api/inventory/^adjust\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^audit/$
   * /api/inventory/^audit\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^relocate/$
   * /api/inventory/^relocate\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^report-damage/$
   * /api/inventory/^report-damage\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^transfer/$
   * /api/inventory/^transfer\.(?P<format>[a-z0-9]+)/?$
   * /api/inventory/^(?P<pk>[^/.]+)/$
   * /api/inventory/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/movements/^allocations/$
   * /api/movements/^allocations\.(?P<format>[a-z0-9]+)/?$
   * /api/movements/^allocations/(?P<pk>[^/.]+)/$
   * /api/movements/^allocations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/movements/^$
   * /api/movements/^\.(?P<format>[a-z0-9]+)/?$
   * /api/movements/^(?P<pk>[^/.]+)/$
   * /api/movements/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/recommendations/^$
   * /api/recommendations/^\.(?P<format>[a-z0-9]+)/?$
   * /api/recommendations/^allocate/$
   * /api/recommendations/^allocate\.(?P<format>[a-z0-9]+)/?$
   * /api/recommendations/^suggest-bin/$
   * /api/recommendations/^suggest-bin\.(?P<format>[a-z0-9]+)/?$
   * /api/recommendations/^(?P<pk>[^/.]+)/$
   * /api/recommendations/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^alerts/$
   * /api/ai/^alerts\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^congestion-risk/$
   * /api/ai/^congestion-risk\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^feedback/$
   * /api/ai/^feedback\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^hotspot-prevention/$
   * /api/ai/^hotspot-prevention\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^operational-scores/$
   * /api/ai/^operational-scores\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^optimize-slotting/$
   * /api/ai/^optimize-slotting\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^predict-demand/$
   * /api/ai/^predict-demand\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^recommendations/$
   * /api/ai/^recommendations\.(?P<format>[a-z0-9]+)/?$
   * /api/ai/^slotting-score/$
   * /api/ai/^slotting-score\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^robot-tasks/$
   * /api/dashboards/^robot-tasks\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^robot-tasks/(?P<pk>[^/.]+)/$
   * /api/dashboards/^robot-tasks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^route-optimizations/$
   * /api/dashboards/^route-optimizations\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^route-optimizations/(?P<pk>[^/.]+)/$
   * /api/dashboards/^route-optimizations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^$
   * /api/dashboards/^\.(?P<format>[a-z0-9]+)/?$
   * /api/dashboards/^(?P<pk>[^/.]+)/$
   * /api/dashboards/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^$
   * /api/orders/^\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^assign-picker/$
   * /api/orders/^assign-picker\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^close/$
   * /api/orders/^close\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^dispatch/$
   * /api/orders/^dispatch\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^generate-picklist/$
   * /api/orders/^generate-picklist\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^optimize-route/$
   * /api/orders/^optimize-route\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^pack/$
   * /api/orders/^pack\.(?P<format>[a-z0-9]+)/?$
   * /api/orders/^(?P<pk>[^/.]+)/$
   * /api/orders/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/product-classifications/^$
   * /api/product-classifications/^\.(?P<format>[a-z0-9]+)/?$
   * /api/product-classifications/^(?P<pk>[^/.]+)/$
   * /api/product-classifications/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/product-dimensions/^storage-rules/$
   * /api/product-dimensions/^storage-rules\.(?P<format>[a-z0-9]+)/?$
   * /api/product-dimensions/^storage-rules/(?P<pk>[^/.]+)/$
   * /api/product-dimensions/^storage-rules/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/product-dimensions/^$
   * /api/product-dimensions/^\.(?P<format>[a-z0-9]+)/?$
   * /api/product-dimensions/^(?P<pk>[^/.]+)/$
   * /api/product-dimensions/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/inbound/^$
   * /api/inbound/^\.(?P<format>[a-z0-9]+)/?$
   * /api/inbound/^(?P<pk>[^/.]+)/$
   * /api/inbound/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/review-queue/
   * /api/ocr/^documents/$
   * /api/ocr/^documents\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/^documents/review-queue/$
   * /api/ocr/^documents/review-queue\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/$
   * /api/ocr/^documents/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/approve/$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/approve\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/reject/$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/reject\.(?P<format>[a-z0-9]+)/?$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/sync-rag/$
   * /api/ocr/^documents/(?P<pk>[^/.]+)/sync-rag\.(?P<format>[a-z0-9]+)/?$

6. **Remaining Backend Gaps**:
   * Missing Swagger documentation for partial APIs.
   * Several APIs missing strict serializer validation and permissions.

7. **Backend Completion %**: 49%
8. **Expected WMS Completion After API Readiness**: 100%
