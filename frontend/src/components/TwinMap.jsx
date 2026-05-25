import React, { useState, useRef } from 'react';
import { Stage, Layer, Rect, Line, Text, Group } from 'react-konva';
import { ZoomIn, ZoomOut, Move } from 'lucide-react';

const TwinMap = ({ activeLayout, occupancyStats, selectedRack, selectRack, suggestedBinId }) => {
  const [scale, setScale] = useState(2);
  const [position, setPosition] = useState({ x: 50, y: 50 });
  const stageRef = useRef(null);

  if (!activeLayout) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 bg-slate-800/40 border border-slate-700/50 rounded-xl backdrop-blur-md">
        Select or upload a warehouse layout to view the digital twin map.
      </div>
    );
  }

  const { zones = [], racks = [], spatial_entities = [], paths = [] } = activeLayout;

  // Zoom Handler
  const handleWheel = (e) => {
    e.evt.preventDefault();
    const scaleBy = 1.15;
    const stage = stageRef.current;
    const oldScale = stage.scaleX();
    const mousePointTo = {
      x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
      y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
    };

    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    if (newScale < 0.5 || newScale > 15) return;

    setScale(newScale);
    setPosition({
      x: (stage.getPointerPosition().x / newScale - mousePointTo.x) * newScale,
      y: (stage.getPointerPosition().y / newScale - mousePointTo.y) * newScale,
    });
  };

  const zoomIn = () => setScale(prev => Math.min(prev * 1.2, 15));
  const zoomOut = () => setScale(prev => Math.max(prev / 1.2, 0.5));
  const resetView = () => {
    setScale(2);
    setPosition({ x: 50, y: 50 });
  };

  // Helper to determine rack occupancy color
  const getRackColor = (rackId) => {
    // Find if suggested bin resides in this rack
    if (suggestedBinId) {
      for (const rack of racks) {
        if (rack.id === rackId) {
          const hasSuggestedBin = rack.shelves?.some(s => s.bins?.some(b => b.id === suggestedBinId));
          if (hasSuggestedBin) return '#a855f7'; // Purple highlight for suggestion
        }
      }
    }

    if (!occupancyStats || !occupancyStats.racks) return '#3b82f6'; // default blue

    const stats = occupancyStats.racks.find(r => r.rack_id === rackId);
    if (!stats) return '#3b82f6';

    const pct = stats.occupancy_percentage;
    if (pct >= 80.0) return '#ef4444'; // Red (Danger/Full)
    if (pct >= 50.0) return '#f97316'; // Orange (Medium)
    return '#22c55e'; // Green (Empty/Available)
  };

  return (
    <div className="relative flex-1 bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl min-h-[500px]">
      {/* Zoom / Pan Controls HUD */}
      <div className="absolute top-4 right-4 z-10 flex gap-2 p-1.5 bg-slate-900/80 border border-slate-700/50 rounded-lg backdrop-blur-md shadow-lg">
        <button onClick={zoomIn} className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition" title="Zoom In">
          <ZoomIn size={18} />
        </button>
        <button onClick={zoomOut} className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition" title="Zoom Out">
          <ZoomOut size={18} />
        </button>
        <button onClick={resetView} className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded transition" title="Recenter Map">
          <Move size={18} />
        </button>
      </div>

      {/* Dynamic Status Legend */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-2 p-3 bg-slate-900/80 border border-slate-700/50 rounded-lg backdrop-blur-md text-xs shadow-lg">
        <div className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Legend</div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded bg-emerald-500 block"></span>
          <span>Available (&lt;50%)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded bg-orange-500 block"></span>
          <span>Medium (&gt;50%)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-200">
          <span className="w-3 h-3 rounded bg-red-500 block"></span>
          <span>Full (&gt;80%)</span>
        </div>
        {suggestedBinId && (
          <div className="flex items-center gap-2 text-slate-200">
            <span className="w-3 h-3 rounded bg-purple-500 animate-pulse block"></span>
            <span className="font-medium text-purple-300">Suggested Bin Target</span>
          </div>
        )}
      </div>

      {/* Main 2D Canvas Stage */}
      <Stage
        width={1000}
        height={600}
        scaleX={scale}
        scaleY={scale}
        x={position.x}
        y={position.y}
        ref={stageRef}
        onWheel={handleWheel}
        draggable
        onDragEnd={(e) => setPosition({ x: e.target.x(), y: e.target.y() })}
        className="cursor-grab active:cursor-grabbing h-full"
      >
        <Layer>
          {/* 1. Render Pathways / Corridors */}
          {paths.map((p) => (
            <Line
              key={p.id}
              points={[parseFloat(p.start_x), parseFloat(p.start_y), parseFloat(p.end_x), parseFloat(p.end_y)]}
              stroke="#334155"
              strokeWidth={parseFloat(p.width) * 2}
              lineCap="round"
              opacity={0.6}
            />
          ))}

          {/* 2. Render Zone Boundaries */}
          {zones.map((z) => {
            const points = z.boundaries?.[0]?.polygon_points || [];
            const flatPoints = points.flatMap(p => [parseFloat(p.x), parseFloat(p.y)]);
            
            return (
              <Group key={z.id}>
                {flatPoints.length >= 4 ? (
                  <Line
                    points={flatPoints}
                    fill="rgba(59, 130, 246, 0.05)"
                    stroke="rgba(59, 130, 246, 0.3)"
                    strokeWidth={0.5}
                    closed
                  />
                ) : (
                  <Rect
                    x={parseFloat(z.x) - parseFloat(z.width)/2}
                    y={parseFloat(z.y) - parseFloat(z.depth)/2}
                    width={parseFloat(z.width)}
                    height={parseFloat(z.depth)}
                    fill="rgba(59, 130, 246, 0.05)"
                    stroke="rgba(59, 130, 246, 0.2)"
                    strokeWidth={0.5}
                  />
                )}
                <Text
                  x={parseFloat(z.x) - 10}
                  y={parseFloat(z.y) - 5}
                  text={z.zone_name}
                  fontSize={4}
                  fill="#94a3b8"
                  opacity={0.7}
                />
              </Group>
            );
          })}

          {/* 3. Render General Obstacles / Pillars */}
          {spatial_entities.map((e) => (
            <Rect
              key={e.id}
              x={parseFloat(e.x) - parseFloat(e.width)/2}
              y={parseFloat(e.y) - parseFloat(e.depth)/2}
              width={parseFloat(e.width)}
              height={parseFloat(e.depth)}
              fill="#1e293b"
              stroke="#475569"
              strokeWidth={0.5}
            />
          ))}

          {/* 4. Render Racks */}
          {racks.map((r) => {
            const isSelected = selectedRack && selectedRack.id === r.id;
            
            return (
              <Group key={r.id} onClick={() => selectRack(r)} onTap={() => selectRack(r)}>
                <Rect
                  x={parseFloat(r.x) - parseFloat(r.width)/2}
                  y={parseFloat(r.y) - parseFloat(r.depth)/2}
                  width={parseFloat(r.width)}
                  height={parseFloat(r.depth)}
                  fill={getRackColor(r.id)}
                  stroke={isSelected ? '#ffffff' : 'rgba(0,0,0,0.2)'}
                  strokeWidth={isSelected ? 1 : 0.3}
                  cornerRadius={0.5}
                  shadowColor="black"
                  shadowBlur={isSelected ? 6 : 2}
                  shadowOpacity={0.3}
                />
                <Text
                  x={parseFloat(r.x) - parseFloat(r.width)/2 + 0.5}
                  y={parseFloat(r.y) - 1}
                  text={r.rack_code}
                  fontSize={2.2}
                  fill={isSelected ? '#ffffff' : '#0f172a'}
                  fontStyle="bold"
                />
              </Group>
            );
          })}
        </Layer>
      </Stage>
    </div>
  );
};

export default TwinMap;
