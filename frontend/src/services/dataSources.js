import api from './api';

export const dataSourcesService = {
  // Get all available data sources
  getAllSources: async () => {
    const response = await api.get('/api/sources');
    return response.data;
  },

  // Get all source types
  getSourceTypes: async () => {
    const response = await api.get('/api/sources_types');
    return response.data;
  },

  // Get source type details
  getSourceTypeDetails: async (name) => {
    const response = await api.get(`/api/sources_types/${name}`);
    return response.data;
  },

  // Test source connectivity
  testSourceConnectivity: async (name, connectionConfig) => {
    const response = await api.post(`/api/sources/${name}/test_connectivity`, connectionConfig);
    return response.data;
  },

  // Create a new data source
  createSource: async (sourceType, sourceData) => {
    const response = await api.post(`/api/sources/${sourceType}/create`, sourceData);
    return response.data;
  },

  // Update a data source
  updateSource: async (sourceId, sourceData) => {
    const response = await api.put(`/api/sources/update/${sourceId}`, sourceData);
    return response.data;
  },

  // Delete a data source
  deleteSource: async (sourceId) => {
    const response = await api.delete(`/api/sources/${sourceId}`);
    return response.data;
  },

  // Get source entities/tables
  getSourceEntities: async (sourceType, connectionConfig) => {
    const response = await api.post(`/api/sources/${sourceType}/entities`, connectionConfig);
    return response.data;
  },

  // Get source details
  getSourceById: async (sourceId) => {
    const response = await api.get(`/api/sources/${sourceId}`);
    return response.data;
  },

  // Get source entities/schema
  getSourceEntitiesById: async (sourceId) => {
    const response = await api.get(`/api/sources/entities/${sourceId}`);
    return response.data;
  },

  // Generate table annotation
  generateTableAnnotation: async (payload) => {
    const response = await api.post('/api/sources/table_annotate', payload);
    return response.data;
  },

  // Upload file
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('media_type', file.type);

    const response = await api.post('/api/sources/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
