import React from 'react';
import { Navigate } from 'react-router-dom';
import authService from '../services/auth';

function AdminRoute({ children }) {
  const isAuthenticated = authService.isAuthenticated();
  const isAdmin = authService.isAdmin();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/home" replace />;
  }

  return children;
}

export default AdminRoute; 