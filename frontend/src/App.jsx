import React, { useState, useEffect } from 'react';
import { useStore } from './store/useStore';
import TwinMap from './components/TwinMap';
import SidebarControls from './components/SidebarControls';
import { LogOut, Layout, BarChart2, CheckCircle2, ShieldAlert } from 'lucide-react';

function App() {
  const {
    token,
    isAuthenticated,
    user,
    layouts,
    activeLayout,
    selectedRack,
    occupancyStats,
    suggestedBinId,
    suggestedBinReason,
    loading,
    error,
    login,
    logout,
    fetchLayouts,
    loadWarehouseTwin,
    uploadLayout,
    suggestBin,
    selectRack
  } = useStore();

  const [username, setUsername] = useState('testuser');
  const [password, setPassword] = useState('testpassword');
  const [activeLayoutId, setActiveLayoutId] = useState('');

  // Auto-fetch layouts list after authentication
  useEffect(() => {
    if (isAuthenticated) {
      fetchLayouts();
    }
  }, [isAuthenticated]);

  // Set default active layout if list changes
  useEffect(() => {
    if (layouts.length > 0) {
      // Find the first layout from the warehouses
      const firstLayout = layouts[0]?.layouts?.[0];
      if (firstLayout) {
        setActiveLayoutId(firstLayout.id);
        loadWarehouseTwin(firstLayout.id);
      }
    }
  }, [layouts]);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    await login(username, password);
  };

  const handleLayoutChange = (e) => {
    const id = e.target.value;
    setActiveLayoutId(id);
    loadWarehouseTwin(id);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[100svh] bg-slate-950 p-4">
        {/* Glassmorphic Login Card */}
        <div className="w-full max-w-md p-8 bg-slate-900/80 border border-slate-800 rounded-2xl shadow-2xl backdrop-blur-md">
          <div className="flex flex-col items-center gap-2 mb-8">
            <div className="p-3 bg-sky-500/10 text-sky-400 rounded-2xl border border-sky-500/20">
              <Layout size={32} />
            </div>
            <h1 className="text-2xl font-bold text-white text-center">Warehouse Twin WMS</h1>
            <p className="text-xs text-slate-400">Sign in to access visual layout control center</p>
          </div>

          <form onSubmit={handleLoginSubmit} className="flex flex-col gap-4 text-sm">
            <div className="flex flex-col gap-1.5">
              <label className="text-slate-300 font-medium">Username / Email</label>
              <input 
                type="text" 
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="p-3 bg-slate-850 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                placeholder="testuser"
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-slate-300 font-medium">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="p-3 bg-slate-850 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="p-3 bg-red-950/40 border border-red-500/30 text-red-400 rounded-lg text-xs flex items-center gap-2">
                <ShieldAlert size={16} />
                <span>{error}</span>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              className="mt-2 p-3 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold rounded-lg transition"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Find all layouts to populate the selection dropdown
  const allLayouts = [];
  layouts.forEach(wh => {
    if (wh.layouts) {
      wh.layouts.forEach(lay => {
        allLayouts.push({ id: lay.id, name: `${lay.layout_name} (${wh.name})` });
      });
    }
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* 1. Header Toolbar */}
      <header className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
            <Layout size={20} />
          </div>
          <span className="font-bold text-white tracking-wide">Intelligent Warehouse Digital Twin</span>
        </div>

        <div className="flex items-center gap-4">
          {allLayouts.length > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-medium">Layout Twin:</span>
              <select 
                value={activeLayoutId} 
                onChange={handleLayoutChange}
                className="p-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-sky-500"
              >
                {allLayouts.map(lay => (
                  <option key={lay.id} value={lay.id}>{lay.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="text-slate-400 text-xs flex items-center gap-1.5">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-ping"></span>
            <span>{user?.full_name || 'WMS Operator'} ({user?.role || 'operator'})</span>
          </div>

          <button 
            onClick={logout} 
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800/50 rounded-lg transition"
            title="Log Out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* 2. Main Analytics & Canvas Layout */}
      <main className="flex-1 flex gap-6 p-6 overflow-hidden max-h-[calc(100vh-73px)]">
        {/* Left Side: Sidebar Controls */}
        <SidebarControls 
          layouts={layouts}
          activeLayout={activeLayout}
          uploadLayout={uploadLayout}
          suggestBin={suggestBin}
          suggestedBinId={suggestedBinId}
          suggestedBinReason={suggestedBinReason}
          selectedRack={selectedRack}
          loading={loading}
        />

        {/* Center: Map Canvas + Top Analytics HUD */}
        <div className="flex-1 flex flex-col gap-6 overflow-hidden">
          {/* Top Analytics Metrics Dashboard */}
          {occupancyStats && (
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Overall Occupancy</div>
                  <div className="text-2xl font-extrabold text-white mt-1">
                    {occupancyStats.overall.occupancy_percentage}%
                  </div>
                </div>
                <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
                  <BarChart2 size={24} />
                </div>
              </div>

              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Occupied Bins</div>
                  <div className="text-2xl font-extrabold text-white mt-1">
                    {occupancyStats.overall.occupied_bins} <span className="text-xs text-slate-500">bins</span>
                  </div>
                </div>
                <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
                  <CheckCircle2 size={24} />
                </div>
              </div>

              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Total capacity</div>
                  <div className="text-2xl font-extrabold text-white mt-1">
                    {occupancyStats.overall.total_bins} <span className="text-xs text-slate-500">bins</span>
                  </div>
                </div>
                <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
                  <Layout size={24} />
                </div>
              </div>
            </div>
          )}

          {/* 2D Canvas Twin Viewer */}
          <TwinMap 
            activeLayout={activeLayout}
            occupancyStats={occupancyStats}
            selectedRack={selectedRack}
            selectRack={selectRack}
            suggestedBinId={suggestedBinId}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
