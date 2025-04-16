import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Base URL para la API
const API_URL = '/api';

// Estado inicial
const initialState = {
  stats: {
    totalClients: 0,
    activeConversations: 0,
    completedOrders: 0,
    totalRevenue: 0,
    clientGrowth: [],
    revenueByDay: []
  },
  recentOrders: [],
  conversations: [],
  isLoading: false,
  error: null
};

// Acción asíncrona para cargar estadísticas del dashboard
export const loadDashboardStats = createAsyncThunk(
  'dashboard/loadStats',
  async (_, { getState, rejectWithValue }) => {
    try {
      const { token } = getState().auth;
      
      if (!token) {
        throw new Error('No hay token de autenticación');
      }
      
      // Configurar el encabezado de autenticación
      const config = {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      };
      
      const response = await axios.get(`${API_URL}/admin/dashboard/stats`, config);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || 
        'Error al cargar estadísticas del dashboard'
      );
    }
  }
);

// Acción asíncrona para cargar órdenes recientes
export const loadRecentOrders = createAsyncThunk(
  'dashboard/loadRecentOrders',
  async (_, { getState, rejectWithValue }) => {
    try {
      const { token } = getState().auth;
      
      if (!token) {
        throw new Error('No hay token de autenticación');
      }
      
      // Configurar el encabezado de autenticación
      const config = {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      };
      
      const response = await axios.get(`${API_URL}/admin/orders/recent`, config);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || 
        'Error al cargar órdenes recientes'
      );
    }
  }
);

// Acción asíncrona para cargar conversaciones activas
export const loadActiveConversations = createAsyncThunk(
  'dashboard/loadActiveConversations',
  async (_, { getState, rejectWithValue }) => {
    try {
      const { token } = getState().auth;
      
      if (!token) {
        throw new Error('No hay token de autenticación');
      }
      
      // Configurar el encabezado de autenticación
      const config = {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      };
      
      const response = await axios.get(`${API_URL}/admin/conversations/active`, config);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || 
        'Error al cargar conversaciones activas'
      );
    }
  }
);

// Slice del dashboard
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearDashboardErrors: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Manejar carga de estadísticas del dashboard
      .addCase(loadDashboardStats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loadDashboardStats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stats = action.payload;
      })
      .addCase(loadDashboardStats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      // Manejar carga de órdenes recientes
      .addCase(loadRecentOrders.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loadRecentOrders.fulfilled, (state, action) => {
        state.isLoading = false;
        state.recentOrders = action.payload;
      })
      .addCase(loadRecentOrders.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      // Manejar carga de conversaciones activas
      .addCase(loadActiveConversations.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loadActiveConversations.fulfilled, (state, action) => {
        state.isLoading = false;
        state.conversations = action.payload;
      })
      .addCase(loadActiveConversations.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  }
});

export const { clearDashboardErrors } = dashboardSlice.actions;
export default dashboardSlice.reducer;