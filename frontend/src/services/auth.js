import axios from 'axios';
import api from './api';

const TOKEN_KEY = 'auth_token';
const USER_ROLE_KEY = 'user_role';
const USERNAME_KEY = 'username';

class AuthService {
    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/token`, formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                withCredentials: true
            });
            
            if (response.data.access_token) {
                localStorage.setItem(TOKEN_KEY, response.data.access_token);
                localStorage.setItem(USER_ROLE_KEY, response.data.role);
                localStorage.setItem(USERNAME_KEY, username);
            }
            
            return response.data;
        } catch (error) {
            throw error.response?.data?.detail || 'An error occurred during login';
        }
    }

    logout() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_ROLE_KEY);
        localStorage.removeItem(USERNAME_KEY);
    }

    getCurrentUser() {
        return localStorage.getItem(USERNAME_KEY);
    }

    getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    isAdmin() {
        return localStorage.getItem(USER_ROLE_KEY) === 'admin';
    }
}

export default new AuthService(); 