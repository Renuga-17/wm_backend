import { create } from 'zustand';
import api from '../utils/api';

export const useStore = create((set, get) => ({
  // Auth state
  token: localStorage.getItem('access_token') || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  user: null,

  // Layouts state
  layouts: [],
  activeLayout: null, // Full twin layout response
  selectedRack: null,
  occupancyStats: null,
  suggestedBinId: null,
  suggestedBinReason: null,

  // Loading & error states
  loading: false,
  error: null,

  // Actions
  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const res = await api.post('/api/users/login/', { username, password });
      const { access, refresh } = res.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      set({ token: access, isAuthenticated: true, error: null });
      // Fetch user profile
      const userRes = await api.get('/api/users/');
      const usersList = userRes.data.results || userRes.data;
      const currentUser = usersList.find(u => u.email.includes(username) || u.username === username) || usersList[0];
      set({ user: currentUser });
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || 'Invalid username or password' });
      return false;
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ token: null, isAuthenticated: false, user: null, activeLayout: null, selectedRack: null });
  },

  fetchLayouts: async () => {
    set({ loading: true });
    try {
      const res = await api.get('/api/layout/entities'); // Wait, let's get layouts
      // Oh, let's fetch warehouses first to list layouts, or layout uploads
      const wRes = await api.get('/api/warehouses/');
      const warehousesList = wRes.data.results || wRes.data;
      
      // Let's get layout files
      // If there are layouts, we will list them
      // Fallback: create mock layout in local list if none exist
      const layoutsList = [];
      for (const wh of warehousesList) {
        if (wh.layouts && wh.layouts.length > 0) {
          layoutsList.push(...wh.layouts);
        }
      }
      set({ layouts: warehousesList });
    } catch (err) {
      console.error(err);
    } finally {
      set({ loading: false });
    }
  },

  loadWarehouseTwin: async (layoutId) => {
    set({ loading: true, error: null, suggestedBinId: null, selectedRack: null });
    try {
      const res = await api.get(`/api/twin/layout/${layoutId}`);
      set({ activeLayout: res.data });
      // Fetch occupancy metrics
      const occRes = await api.get('/api/twin/occupancy');
      set({ occupancyStats: occRes.data });
    } catch (err) {
      set({ error: 'Failed to load warehouse digital twin.' });
    } finally {
      set({ loading: false });
    }
  },

  uploadLayout: async (warehouseId, layoutName, file) => {
    set({ loading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('warehouse_id', warehouseId);
      formData.append('layout_name', layoutName);
      formData.append('file', file);
      
      const res = await api.post('/api/layout/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // After upload, trigger analyze
      await get().analyzeLayout(res.data.id);
      return res.data.id;
    } catch (err) {
      set({ error: 'Failed to upload layout drawing.' });
      return null;
    } finally {
      set({ loading: false });
    }
  },

  analyzeLayout: async (layoutId) => {
    set({ loading: true, error: null });
    try {
      await api.post('/api/layout/analyze', { layout_id: layoutId });
      // Reload the twin representation
      await get().loadWarehouseTwin(layoutId);
    } catch (err) {
      set({ error: 'Failed to extract layout coordinates.' });
    } finally {
      set({ loading: false });
    }
  },

  suggestBin: async (productId, quantity) => {
    set({ loading: true, error: null, suggestedBinId: null });
    try {
      const res = await api.post('/api/recommendations/suggest-bin/', {
        product_id: productId,
        quantity: parseInt(quantity)
      });
      if (res.data.success) {
        set({
          suggestedBinId: res.data.recommended_bin_id,
          suggestedBinReason: res.data.reasoning
        });
        return res.data.recommended_bin_id;
      }
    } catch (err) {
      set({ error: 'AI Recommendation service is currently offline.' });
    } finally {
      set({ loading: false });
    }
  },

  selectRack: (rack) => {
    set({ selectedRack: rack });
  }
}));
