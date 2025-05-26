import api from './api';

export const sopService = {
  getAllSOPs: async (searchCondition = '', pageSize = 10, pageNum = 1) => {
    const response = await api.get('/api/sops', {
      params: { search_condition: searchCondition, page_size: pageSize, page_num: pageNum }
    });
    return response.data;
  },

  getSOP: async (sopId) => {
    const response = await api.get(`/api/sops/${sopId}`);
    return response.data;
  },

  createSOP: async (sopData) => {
    const response = await api.post('/api/sops', sopData);
    return response.data;
  },

  updateSOP: async (sopId, sopData) => {
    const response = await api.put(`/api/sops/${sopId}`, sopData);
    return response.data;
  },

  deleteSOP: async (sopId) => {
    const response = await api.delete(`/api/sops/${sopId}`);
    return response.data;
  }
}; 