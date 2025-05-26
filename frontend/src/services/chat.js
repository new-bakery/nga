import api from './api';
import { v4 as uuidv4 } from 'uuid';
import { uploadImage } from './api';

export const chatService = {
  // Load all chat sessions
  loadSessions: async () => {
    try {
      const response = await api.get('/api/conversations');
      // Ensure all sessions have createdAt in ISO string format
      const sessions = response.data.map(session => ({
        ...session,
        timestamp: session.created_at || new Date().toISOString()
      }));
      return sessions;
    } catch (error) {
      console.error('Error loading sessions:', error);
      throw error;
    }
  },

  // Create a new session
  createSession: () => {
    return {
      id: -1,
      messages: [],
      dataSourceIds: [], // Initialize with empty array
      timestamp: new Date().toISOString()
    };
  },

  // Get a session
  getSession: async (sessionId) => {
    try {
      return await api.get(`/api/conversations/${sessionId}`);
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  },

  // Delete a session
  deleteSession: async (sessionId) => {
    try {
      // Note: This API should only be called for sessions with messages
      await api.delete(`/api/conversations/${sessionId}`);
      return true;
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  },

  // Upload an image
  uploadChatImage: async (file) => {
    try {
      const response = await uploadImage(file);
      return response.url; // Assuming the backend returns { url: "..." }
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  },

  // Send a message and get response
  sendMessage: async (message, imageUrl, sessionId, currentMessages, dataSourceIds, useSop) => {
    try {
      const response = await api.post(`/api/conversations/${sessionId}/chat?user_request=${message}&use_sop=${useSop}`, 
        dataSourceIds.map((sourceId) => {
          return {
            "source_id": sourceId,
            "source_name": "string"
          }
        }), {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }
};

export default chatService; 