import React, { useState, useEffect } from 'react';
import { adminService } from '../../../services/admin';
import Modal from '../../../components/Modal/Modal';
import './UserManagement.scss';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    role: 'user',
    password: ''
  });
  const [searchForm, setSearchForm] = useState({
    username: '',
    email: ''
  });
  const [userData, setUserData] = useState([]);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const data = await adminService.getUsers();
      setUsers(data);
      setUserData(data);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearchInputChange = (e) => {
    const { name, value } = e.target;
    setSearchForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        await adminService.updateUser(editingUser.id, formData);
      } else {
        await adminService.createUser(formData);
      }
      loadUsers();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      role: user.role || 'user',
      status: user.status || 'active',
      password: ''
    });
    setShowAddModal(true);
  };

  const handleDeleteClick = (user) => {
    setUserToDelete(user);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;
    
    try {
      await adminService.deleteUser(userToDelete.id);
      await loadUsers(); // Reload the full user list after deletion
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Failed to delete user. Please try again.');
    }
    setShowDeleteModal(false);
    setUserToDelete(null);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingUser(null);
    setFormData({
      username: '',
      email: '',
      role: 'user',
      password: ''
    });
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const filteredData = await adminService.getUsers(searchForm);
      setUserData(filteredData);
    } catch (error) {
      console.error('Error searching users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSearchForm({
      username: '',
      email: ''
    });
    loadUsers();
  };

  return (
    <div className="user-management">
      <div className="header">
        <h2>User Management</h2>
        <div className="action-buttons">
          <button 
            className="add-user-btn" 
            onClick={() => setShowAddModal(true)}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Add User
          </button>
        </div>
      </div>

      <div className="search-filter">
        <form onSubmit={handleSearch}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <div className="input-with-icon">
              <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
              <input 
                type="text" 
                id="username" 
                name="username" 
                placeholder="Please enter username" 
                value={searchForm.username}
                onChange={handleSearchInputChange}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <div className="input-with-icon">
              <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
              <input 
                type="text" 
                id="email" 
                name="email" 
                placeholder="Please enter email" 
                value={searchForm.email}
                onChange={handleSearchInputChange}
              />
            </div>
          </div>
                    
          <div className="filter-buttons">
            <button type="submit" className="search-btn">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              Search
            </button>
            <button type="button" className="reset-btn" onClick={handleReset}>
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <polyline points="1 4 1 10 7 10"></polyline>
                <polyline points="23 20 23 14 17 14"></polyline>
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
              </svg>
              Reset
            </button>
          </div>
        </form>
      </div>

      <div className="user-table">
        {isLoading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Id</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {userData.length > 0 ? (
                userData.map(user => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>{user.role}</td>                    
                    <td>
                      <div className="table-actions">
                        <button 
                          className="edit-btn" 
                          onClick={() => handleEdit(user)} 
                          title="Edit"
                        >
                          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                          </svg>
                        </button>
                        <button 
                          className="delete-btn" 
                          onClick={() => handleDeleteClick(user)}
                          title="Delete"
                        >
                          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="no-data">
                    No data found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
        
        <div className="pagination">
          <div className="page-info">
            Total {userData.length} records
          </div>
          <div className="page-controls">
            <button className="page-btn" disabled>
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </button>
            <span className="page-number active">1</span>
            <button className="page-btn" disabled>
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>
          </div>
        </div>
      </div>

      {showAddModal && (
        <div className="modal-overlay">
          <div className="user-modal">
            <div className="modal-header">
              <h3>{editingUser ? "Edit User" : "Add User"}</h3>
              <button className="close-btn" onClick={handleCloseModal}>
                <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div className="modal-body">
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="modal-username">Username</label>
                  <div className="input-with-icon">
                    <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                      <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                    <input 
                      type="text" 
                      id="modal-username" 
                      name="username" 
                      placeholder="Please enter username" 
                      value={formData.username} 
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label htmlFor="modal-email">Email</label>
                  <div className="input-with-icon">
                    <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                      <polyline points="22,6 12,13 2,6"></polyline>
                    </svg>
                    <input 
                      type="email" 
                      id="modal-email" 
                      name="email" 
                      placeholder="Please enter email" 
                      value={formData.email} 
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>
                
                <div className="form-group">
                  <label htmlFor="modal-role">Role</label>
                  <div className="input-with-icon">
                    <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    <select
                      id="modal-role"
                      name="role"
                      value={formData.role}
                      onChange={handleInputChange}
                      className="role-select"
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>
                
                
                <div className="form-group">
                  <label htmlFor="modal-password">Password</label>
                  <div className="input-with-icon">
                    <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    <input 
                      type="password" 
                      id="modal-password" 
                      name="password" 
                      placeholder="Please enter password" 
                      value={formData.password} 
                      onChange={handleInputChange}
                      required={!editingUser}
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="button" className="cancel-btn" onClick={handleCloseModal}>
                    Cancel
                  </button>
                  <button type="submit" className="submit-btn">
                    Confirm
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete User"
        message={`Are you sure you want to delete user "${userToDelete?.username}"? This action cannot be undone.`}
      />
    </div>
  );
};

export default UserManagement; 