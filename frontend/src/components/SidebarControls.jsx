import React, { useState, useEffect } from 'react';
import { Upload, Cpu, Layers, Tag, Box } from 'lucide-react';
import api from '../utils/api';

const SidebarControls = ({ 
  layouts, 
  activeLayout, 
  uploadLayout, 
  suggestBin, 
  suggestedBinId, 
  suggestedBinReason, 
  selectedRack, 
  loading 
}) => {
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouseId, setSelectedWarehouseId] = useState('');
  const [layoutName, setLayoutName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [quantity, setQuantity] = useState('10');

  useEffect(() => {
    // Fetch warehouses for upload dropdown
    api.get('/api/warehouses/')
      .then(res => {
        const list = res.data.results || res.data;
        setWarehouses(list);
        if (list.length > 0) setSelectedWarehouseId(list[0].id);
      })
      .catch(err => console.error(err));

    // Fetch products for recommendation form
    api.get('/api/products/')
      .then(res => {
        const list = res.data.results || res.data;
        setProducts(list);
        if (list.length > 0) setSelectedProductId(list[0].id);
      })
      .catch(err => console.error(err));
  }, []);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedWarehouseId || !layoutName || !selectedFile) return;
    await uploadLayout(selectedWarehouseId, layoutName, selectedFile);
    setLayoutName('');
    setSelectedFile(null);
  };

  const handleRecommendSubmit = async (e) => {
    e.preventDefault();
    if (!selectedProductId || !quantity) return;
    await suggestBin(selectedProductId, quantity);
  };

  return (
    <div className="w-[380px] flex flex-col gap-6 p-5 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-y-auto max-h-[85vh]">
      {/* 1. CAD Ingest / Layout Upload Panel */}
      <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl">
        <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-sky-400">
          <Upload size={18} />
          <span>Upload Warehouse layout</span>
        </div>
        <form onSubmit={handleUploadSubmit} className="flex flex-col gap-3 text-xs">
          <div className="flex flex-col gap-1">
            <label className="text-slate-400">Target Warehouse</label>
            <select 
              value={selectedWarehouseId} 
              onChange={e => setSelectedWarehouseId(e.target.value)}
              className="p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-sky-500"
            >
              {warehouses.map(w => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-slate-400">Layout Name</label>
            <input 
              type="text" 
              placeholder="e.g. Floorplan Main" 
              value={layoutName}
              onChange={e => setLayoutName(e.target.value)}
              className="p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-sky-500"
              required
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-slate-400">CAD Drawing (DXF) or Image</label>
            <input 
              type="file" 
              onChange={e => setSelectedFile(e.target.files[0])}
              className="text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="mt-1 p-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Ingest & Analyze'}
          </button>
        </form>
      </div>

      {/* 2. AI Recommendation Portal */}
      <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl">
        <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-purple-400">
          <Cpu size={18} />
          <span>AI Bin Allocator</span>
        </div>
        <form onSubmit={handleRecommendSubmit} className="flex flex-col gap-3 text-xs">
          <div className="flex flex-col gap-1">
            <label className="text-slate-400">Select Product</label>
            <select 
              value={selectedProductId} 
              onChange={e => setSelectedProductId(e.target.value)}
              className="p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-purple-500"
            >
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.sku} - {p.product_name}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-slate-400">Quantity</label>
            <input 
              type="number" 
              value={quantity}
              onChange={e => setQuantity(e.target.value)}
              className="p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-purple-500"
              min="1"
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="mt-1 p-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            {loading ? 'Allocating...' : 'Get Suggestion'}
          </button>
        </form>

        {/* Suggestion Result HUD */}
        {suggestedBinId && (
          <div className="mt-3 p-3 bg-purple-950/40 border border-purple-500/30 rounded-lg text-xs animate-fadeIn">
            <div className="font-semibold text-purple-300 mb-1 flex items-center gap-1">
              <Box size={14} />
              <span>Recommended Bin Location:</span>
            </div>
            <div className="font-bold text-white text-sm bg-purple-900/40 p-1.5 rounded text-center border border-purple-500/20 mb-2">
              {suggestedBinId}
            </div>
            <p className="text-[11px] text-slate-300 leading-normal">
              <span className="font-semibold text-purple-400">Reasoning:</span> {suggestedBinReason}
            </p>
          </div>
        )}
      </div>

      {/* 3. Selected Rack Visual Inspector */}
      <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl flex-1 min-h-[220px] flex flex-col">
        <div className="flex items-center gap-2 mb-3 text-sm font-semibold text-emerald-400">
          <Layers size={18} />
          <span>Rack Inspector</span>
        </div>

        {selectedRack ? (
          <div className="flex flex-col gap-4 text-xs flex-1">
            <div className="flex justify-between items-center bg-slate-850 p-2 rounded">
              <span className="font-bold text-white">{selectedRack.rack_code}</span>
              <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">Max: {selectedRack.max_weight}kg</span>
            </div>

            {/* Render Shelves */}
            <div className="flex flex-col gap-3 overflow-y-auto max-h-[280px] pr-1">
              {selectedRack.shelves?.map(s => (
                <div key={s.id} className="p-2 bg-slate-900 border border-slate-800 rounded">
                  <div className="text-[10px] text-slate-400 font-semibold mb-1.5 flex justify-between">
                    <span>Level {s.shelf_number}</span>
                    <span>Height: {s.height_from_ground}m</span>
                  </div>
                  <div className="grid grid-cols-4 gap-1.5">
                    {s.bins?.map(b => (
                      <div 
                        key={b.id} 
                        className={`p-1.5 rounded text-center border text-[9px] font-bold ${
                          b.id === suggestedBinId 
                            ? 'bg-purple-600/30 border-purple-400 text-purple-200 animate-pulse' 
                            : b.is_occupied 
                              ? 'bg-red-500/20 border-red-500/30 text-red-400' 
                              : 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'
                        }`}
                        title={`Bin Code: ${b.bin_code}\nCapacity: ${b.current_capacity}/${b.max_capacity}`}
                      >
                        {b.bin_code.split('-').pop()}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 text-xs text-center">
            Click any rack on the warehouse map to inspect its shelf levels and bins.
          </div>
        )}
      </div>
    </div>
  );
};

export default SidebarControls;
