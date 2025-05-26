import React, { useState, useEffect } from 'react';
import { adminService } from '../../../services/admin';
import NewSourceWizard from '../../../components/Panel/ManagePanel/NewSourceWizard/NewSourceWizard';
import EditSourceWizard from '../../../components/Panel/ManagePanel/EditSourceWizard/EditSourceWizard';
import Modal from '../../../components/Modal/Modal';
import './DataSourceManagement.scss';

function DataSourceManagement() {
  const [dataSources, setDataSources] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNewSourceWizard, setShowNewSourceWizard] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState(null);
  const [error, setError] = useState(null);
  const [searchForm, setSearchForm] = useState({
    name: '',
    type: ''
  });

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    setIsLoading(true);
    try {
      const data = await adminService.getAllDataSources();
      setDataSources(data);
    } catch (error) {
      console.error('Error loading data sources:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateSource = async (newSource) => {
    try {
      await adminService.createSystemDataSource(newSource);
      loadDataSources();
      setShowNewSourceWizard(false);
    } catch (error) {
      console.error('Error creating data source:', error);
      setError('Failed to create data source');
    }
  };

  const handleEditSource = async () => {
    // This function is now just used to refresh the list after editing
    await loadDataSources();
    setEditingSource(null);
  };

  const handleDeleteClick = (source) => {
    setSourceToDelete(source);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!sourceToDelete) return;
    
    try {
      await adminService.deleteAnyDataSource(sourceToDelete.id);
      setDataSources(dataSources.filter(s => s.id !== sourceToDelete.id));
    } catch (err) {
      setError('Failed to delete data source');
      console.error('Error deleting data source:', err);
    }
    setShowDeleteModal(false);
    setSourceToDelete(null);
  };
  
  const handleSearchInputChange = (e) => {
    const { name, value } = e.target;
    setSearchForm(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      // Filter locally in this example - in a real app this would call an API
      let filteredData = await adminService.getAllDataSources();
      
      if (searchForm.name) {
        filteredData = filteredData.filter(source => 
          source.source_name.toLowerCase().includes(searchForm.name.toLowerCase())
        );
      }
      
      if (searchForm.type) {
        filteredData = filteredData.filter(source => 
          source.source_type.toLowerCase() === searchForm.type.toLowerCase()
        );
      }
      
      setDataSources(filteredData);
    } catch (error) {
      console.error('Error searching data sources:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleReset = () => {
    setSearchForm({
      name: '',
      type: ''
    });
    loadDataSources();
  };

  return (
    <div className="datasource-management">
      <div className="page-header">
        <h2>Data Source Management</h2>
        <button 
          className="add-button"
          onClick={() => setShowNewSourceWizard(true)}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Add Data Source
        </button>
      </div>

      <div className="search-filter">
        <form onSubmit={handleSearch}>
          <div className="form-group">
            <label htmlFor="name">Source Name</label>
            <div className="input-with-icon">
              <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
              </svg>
              <input 
                type="text" 
                id="name" 
                name="name" 
                placeholder="Search by name" 
                value={searchForm.name}
                onChange={handleSearchInputChange}
              />
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="type">Source Type</label>
            <div className="input-with-icon">
              <svg className="input-icon" viewBox="0 0 24 24" width="18" height="18" stroke="#bbb" strokeWidth="2" fill="none">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
              </svg>
              <select 
                id="type" 
                name="type" 
                value={searchForm.type}
                onChange={handleSearchInputChange}
              >
                <option value="">All Types</option>
                <option value="database">Database</option>
                <option value="file">File</option>
                <option value="api">API</option>
              </select>
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

      <div className="datasources-table">
        {isLoading ? (
          <div className="loading">Loading data sources...</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Data Source Type</th>
                <th>Visibility</th>
                <th>Owner</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {dataSources.length > 0 ? (
                dataSources.sort((a, b) => a.source_name.localeCompare(b.source_name)).map(source => (
                  <tr key={source.id}>
                    <td>{source.source_name}</td>
                    <td>{source.source_type}</td>
                    <td>
                      <span className={`status-badge ${source.is_private ? 'private' : 'public'}`}>
                        {source.is_private ? 'Private' : 'Public'}
                      </span>
                    </td>
                    <td>{source.user_id}</td>
                    <td>
                      <div className="actions">
                        <button
                          className="edit-button"
                          onClick={() => setEditingSource(source)}
                          title="Edit source"
                        >
                          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                          </svg>
                        </button>
                        <button
                          className="delete-button"
                          onClick={() => handleDeleteClick(source)}
                          title="Delete source"
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
                  <td colSpan="5" className="no-data">
                    No data sources found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
        
        <div className="pagination">
          <div className="page-info">
            Total {dataSources.length} records
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

      {/* New Source Wizard Modal */}
      {showNewSourceWizard && (
        <NewSourceWizard
          onClose={() => setShowNewSourceWizard(false)}
          onCreateSource={loadDataSources}
          isAdminContext={true}
        />
      )}

      {/* Edit Source Wizard Modal */}
      {editingSource && (
        <EditSourceWizard
          sourceId={editingSource.id}
          onClose={() => setEditingSource(null)}
          onUpdateSource={handleEditSource}
        />
      )}

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Data Source"
        message={`Are you sure you want to delete "${sourceToDelete?.source_name}"? This action cannot be undone.`}
      />
      
      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-error">
            <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}

export default DataSourceManagement; 