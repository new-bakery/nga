import api from './api';

export const adminService = {
  // User Management
  getUsers: async () => {
    try {
      const response = await api.get('/api/admin/users');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch users');
    }
  },

  createUser: async (userData) => {
    try {
      const response = await api.post('/api/admin/users', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create user');
    }
  },

  updateUser: async (userId, userData) => {
    try {
      const response = await api.put(`/api/admin/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update user');
    }
  },

  deleteUser: async (userId) => {
    try {
      const response = await api.delete(`/api/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete user');
    }
  },

  // Data Source Management
  getAllDataSources: async () => {
    try {
      const response = await api.get('/api/admin/sources');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch data sources');
    }
  },

  createSystemDataSource: async (sourceData) => {
    try {
      const response = await api.post('/api/admin/sources', sourceData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create data source');
    }
  },

  updateAnyDataSource: async (sourceId, sourceData) => {
    try {
      const response = await api.put(`/api/admin/sources/${sourceId}`, sourceData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update data source');
    }
  },

  deleteAnyDataSource: async (sourceId) => {
    try {
      const response = await api.delete(`/api/admin/sources/${sourceId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete data source');
    }
  }
}; 