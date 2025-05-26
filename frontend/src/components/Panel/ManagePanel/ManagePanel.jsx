import React, { useState, useEffect } from 'react';
import { 
  Database, 
  ChevronRight,
  Plus,
  X,
  Search
} from 'react-feather';
import NewSourceWizard from './NewSourceWizard/NewSourceWizard';
import { DATA_SOURCE_TYPES } from '../../../constants/dataSources';
import { dataSourcesService } from '../../../services/dataSources';
import './ManagePanel.scss';
import Modal from '../../Modal/Modal';

// Mock data for available data sources
const MOCK_AVAILABLE_SOURCES = {
  excel: [
    { id: 'excel-1', name: 'Sales Data 2023.xlsx', type: 'excel' },
    { id: 'excel-2', name: 'Customer Analytics.xlsx', type: 'excel' },
    { id: 'excel-3', name: 'Product Inventory.xlsx', type: 'excel' }
  ],
  mysql: [
    { id: 'mysql-1', name: 'Production Database', type: 'mysql' },
    { id: 'mysql-2', name: 'Customer Database', type: 'mysql' }
  ],
  postgresql: [
    { id: 'postgresql-1', name: 'Analytics DB', type: 'postgresql' },
    { id: 'postgresql-2', name: 'Metrics DB', type: 'postgresql' }
  ]
};

function ManagePanel({ isCollapsed, onToggleCollapse, onClose, selectedSources = [], onUpdateSources }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewSourceWizard, setShowNewSourceWizard] = useState(false);
  const [sources, setSources] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [sourceToDelete, setSourceToDelete] = useState(null);
  
  // Add a ref to track if the component is mounted
  const isMounted = React.useRef(false);

  useEffect(() => {
    // Skip the first render in strict mode
    if (!isMounted.current) {
      isMounted.current = true;
      loadDataSources();
    }
    
    // Cleanup function
    return () => {
      isMounted.current = false;
    };
  }, []); // Empty dependency array

  const loadDataSources = async () => {
    if (!isLoading) setIsLoading(true);
    setError(null);
    
    try {
      const dataSources = await dataSourcesService.getAllSources();
      // Only update state if component is still mounted
      if (isMounted.current) {
        // Transform the data sources to match the expected format
        const transformedSources = dataSources.map(source => ({
          id: source.id,
          name: source.source_name,
          type: source.source_type,
          source_type: source.is_private ? 'user' : 'system',
          description: source.description,
          connection: source.connection,
          status: source.status
        }));
        setSources(transformedSources);
      }
    } catch (err) {
      if (isMounted.current) {
        setError('Failed to load data sources');
        console.error('Error loading data sources:', err);
      }
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  };

  const handleSourceSelect = (source) => {
    if (selectedSources.includes(source.id)) {
      onUpdateSources(selectedSources.filter(id => id !== source.id));
    } else {
      onUpdateSources([...selectedSources, source.id]);
    }
  };

  const handleCreateSource = async () => {
    loadDataSources();
  };

  const handleDeleteClick = (source) => {
    setSourceToDelete(source);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!sourceToDelete) return;
    
    try {
      await dataSourcesService.deleteSource(sourceToDelete.id);
      setSources(prevSources => prevSources.filter(source => source.id !== sourceToDelete.id));
      if (selectedSources.includes(sourceToDelete.id)) {
        onUpdateSources(selectedSources.filter(id => id !== sourceToDelete.id));
      }
    } catch (error) {
      console.error('Error deleting data source:', error);
      alert('Failed to delete data source. Please try again.');
    }
    setShowDeleteModal(false);
    setSourceToDelete(null);
  };

  // Filter sources based on search query
  const filteredSources = sources.filter(source => 
    source.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <div className={`manage-panel ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="manage-panel-header">
          <h2>Data Sources</h2>
          <div className="panel-controls">
            <button 
              className="collapse-button" 
              onClick={onToggleCollapse}
              title={isCollapsed ? "Configure data sources" : "Collapse panel"}
              aria-label={isCollapsed ? "Configure data sources" : "Collapse panel"}
            >
              {isCollapsed ? <Database size={18} /> : <ChevronRight size={18} />}
            </button>
          </div>
        </div>

        <div className="manage-panel-content">
          {/* Selected Data Sources Section */}
          <section className="selected-sources-section">
            <div className="section-header">
              <h3>Selected Sources</h3>
            </div>
            <div className="selected-sources-list">
              {selectedSources.map(sourceId => {
                // Find the full source object from the sources array
                const source = sources.find(s => s.id === sourceId);
                if (!source) return null; // Skip if source not found
                
                const IconComponent = DATA_SOURCE_TYPES.find(t => t.id === source.type)?.icon;
                return (
                  <div key={sourceId} className="selected-source-item" role="listitem">
                    <span className="source-icon" title={`${source.type} source`}>
                      {IconComponent && <IconComponent size={18} />}
                    </span>
                    <span className="source-name" title={source.name}>{source.name}</span>
                    {/* <span className={`source-type-indicator ${source.source_type}`} title={`${source.source_type === 'system' ? 'System' : 'Custom'} source`}>
                      {source.source_type === 'system' ? 'System' : 'Custom'}
                    </span> */}
                    <button 
                      className="remove-source-button"
                      onClick={() => handleSourceSelect(source)}
                      title="Remove source"
                      aria-label={`Remove ${source.name}`}
                    >
                      <X size={18} />
                    </button>
                  </div>
                );
              })}
              {selectedSources.length === 0 && (
                <div className="empty-state" role="status">No data sources selected</div>
              )}
            </div>
          </section>

          {/* Available Data Sources Section */}
          <section className="available-sources-section">
            <h3>Available Data Sources</h3>
            
            {/* Search Box */}
            <div className="search-container">
              <input
                type="text"
                placeholder="Search data sources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
                aria-label="Search data sources"
              />
            </div>

            {/* New Source Button */}
            <button 
              className="new-source-button"
              onClick={() => setShowNewSourceWizard(true)}
              aria-label="Add new data source"
            >
              <Plus size={18} /> Add New Data Source
            </button>

            {/* Available Sources List */}
            <div className="available-sources-list" role="list">
              {filteredSources.sort((a, b) => a.name.localeCompare(b.name)).map(source => {
                const IconComponent = DATA_SOURCE_TYPES.find(t => t.id === source.type)?.icon;
                const isSelected = selectedSources.includes(source.id);
                const canDelete = source.source_type === 'user';
                
                return (
                  <div 
                    key={source.id} 
                    className="available-source-item"
                    role="listitem"
                  >
                    <span className="source-icon" title={`${source.type} source`}>
                      {IconComponent && <IconComponent size={18} />}
                    </span>
                    <span className="source-name" title={source.name}>{source.name}</span>
                    {/* <span className={`source-type-indicator ${source.source_type}`} title={`${source.source_type === 'system' ? 'System' : 'Custom'} source`}>
                      {source.source_type === 'system' ? 'System' : 'Custom'}
                    </span> */}
                    <div className="source-actions">
                      {!isSelected && (
                        <button 
                          className="add-button"
                          onClick={() => handleSourceSelect(source)}
                          title="Add to selected sources"
                          aria-label={`Add ${source.name}`}
                        >
                          <Plus size={16} />
                        </button>
                      )}
                      {canDelete && (
                        <button 
                          className="delete-button"
                          onClick={() => handleDeleteClick(source)}
                          title="Delete source"
                          aria-label={`Delete ${source.name}`}
                        >
                          <X size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              {filteredSources.length === 0 && (
                <div className="empty-state" role="status">
                  {searchQuery ? 'No matching data sources found' : 'No data sources available'}
                </div>
              )}
            </div>
          </section>

          {/* Loading and Error States */}
          {isLoading && (
            <div className="loading-state" role="status">
              Loading data sources...
            </div>
          )}
          
          {error && (
            <div className="error-state" role="alert">
              {error}
            </div>
          )}
        </div>

        <Modal
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDeleteConfirm}
          title="Delete Data Source"
          message={`Are you sure you want to delete "${sourceToDelete?.name}"? This action cannot be undone.`}
        />
      </div>

      {showNewSourceWizard && (
        <NewSourceWizard
          onClose={() => setShowNewSourceWizard(false)}
          onCreateSource={handleCreateSource}
          isAdminContext={false}
        />
      )}
    </>
  );
}

export default ManagePanel; 