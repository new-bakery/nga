import React, { useState, useEffect, useCallback, useRef } from 'react';
import { X, ChevronDown, ChevronUp, Loader, Search, Plus, AlertCircle, Upload, Check } from 'react-feather';
import { dataSourcesService } from '../../../../services/dataSources';
import './EditSourceWizard.scss';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';

const TABS = {
  CONFIGURE_SOURCE: 'CONFIGURE_SOURCE',
  CONFIGURE_SCHEMA: 'CONFIGURE_SCHEMA',
};

const APP_LANG = import.meta.env.VITE_APP_LANG || 'en';

// Animation variants
const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3 } }
};

const slideUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } }
};

const slideRight = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0, transition: { type: "spring", stiffness: 100 } }
};

const FileUploader = ({ fieldInfo, existingFiles = [], onFilesUploaded, disabled = false }) => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFileObjects, setUploadedFileObjects] = useState(existingFiles);

  useEffect(() => {
    setUploadedFileObjects(existingFiles);
  }, [existingFiles]);

  // ... rest of FileUploader implementation ...
};

const EditSourceWizard = ({ sourceId, onClose, onUpdateSource }) => {
  const [activeTab, setActiveTab] = useState(TABS.CONFIGURE_SOURCE);
  const [source, setSource] = useState(null);
  const [sourceEntities, setSourceEntities] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [expandedTables, setExpandedTables] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTables, setSelectedTables] = useState(new Set());
  const errorRef = useRef(null);
  const [generatingAnnotations, setGeneratingAnnotations] = useState({});
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    connectionInfo: {},
    isPrivate: false,
  });
  const [columnDescriptions, setColumnDescriptions] = useState({});
  
  // Add ref for modal animation
  const modalRef = useRef(null);

  useEffect(() => {
    const fetchSourceData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const sourceData = await dataSourcesService.getSourceById(sourceId);
        setSource(sourceData);

        // Transform the connection info to handle file objects correctly
        let connectionInfo = sourceData.connection || {};
        if (sourceData.source_type === 'tabularfile' && sourceData.connection?.file_objects) {
          connectionInfo = {
            'Tabular Files': {
              file_objects: sourceData.connection.file_objects
            }
          };
        }

        setFormData({
          name: sourceData.source_name,
          description: sourceData.description?.find(desc => desc.lang === APP_LANG)?.text || '',
          connectionInfo: connectionInfo,
          isPrivate: sourceData.is_private
        });
      } catch (err) {
        setError('Failed to fetch source details. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSourceData();
  }, [sourceId]);

  useEffect(() => {
    const fetchSourceEntities = async () => {
      if (activeTab === TABS.CONFIGURE_SCHEMA) {
        try {
          setIsLoading(true);
          setError(null);
          const response = await dataSourcesService.getSourceEntitiesById(sourceId);
          const entities = response.data?.tables || [];
          setSourceEntities(entities);

          // Initialize selected tables based on _selected field
          const selectedTableSet = new Set(
            entities.filter(table => table._selected).map(table => table.table_name)
          );
          setSelectedTables(selectedTableSet);

          // Initialize column descriptions
          const descriptions = {};
          entities.forEach(table => {
            table.columns.forEach(column => {
              descriptions[`${table.table_name}.${column.column_name}`] =
                column.description?.find(desc => desc.lang === APP_LANG)?.text || '';
            });
          });
          setColumnDescriptions(descriptions);
        } catch (err) {
          setError('Failed to fetch schema details. Please try again.');
        } finally {
          setIsLoading(false);
        }
      }
    };

    fetchSourceEntities();
  }, [sourceId, activeTab]);

  useEffect(() => {
    if (error && errorRef.current) {
      errorRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [error]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleConnectionInfoChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      connectionInfo: {
        ...prev.connectionInfo,
        [field]: field === 'Tabular Files' ? { file_objects: value } : value,
      },
    }));
  };

  const handleColumnDescriptionChange = (tableName, columnName, description) => {
    setColumnDescriptions(prev => ({
      ...prev,
      [`${tableName}.${columnName}`]: description,
    }));
  };

  const toggleTableExpansion = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName],
    }));
  };

  const toggleTableSelection = (tableName) => {
    setSelectedTables(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(tableName)) {
        newSelected.delete(tableName);
      } else {
        newSelected.add(tableName);
      }
      return newSelected;
    });
    
    // Also update the _selected flag in the sourceEntities
    if (sourceEntities) {
      setSourceEntities(prev => 
        prev.map(table => 
          table.table_name === tableName 
            ? { ...table, _selected: !selectedTables.has(tableName) } 
            : table
        )
      );
    }
  };

  const handleGenerateAnnotation = async (table) => {
    setGeneratingAnnotations(prev => ({ ...prev, [table.table_name]: true }));
    try {
      const payload = {
        lang: [APP_LANG],
        source_name: formData.name || "",
        source_description: [{
          lang: APP_LANG,
          text: formData.description || ""
        }],
        entity: {
          table_name: table.table_name,
          description: table.description || [{
            lang: APP_LANG,
            text: ""
          }],
          domains: table.domains || [],
          tags: table.tags || "",
          columns: table.columns.map(col => ({
            column_name: col.column_name,
            type: col.type,
            description: col.description || [{
              lang: APP_LANG,
              text: ""
            }],
            tags: col.tags || ""
          })),
          primary_keys: table.primary_keys || [],
          foreign_keys: table.foreign_keys || []
        }
      };

      const response = await dataSourcesService.generateTableAnnotation(payload);
      const annotations = response[APP_LANG];

      // Update table and column descriptions
      setSourceEntities(prev =>
        prev.map(t => {
          if (t.table_name === table.table_name) {
            const updatedTable = {
              ...t,
              description: [{
                lang: APP_LANG,
                text: annotations.table_description
              }]
            };
            updatedTable.columns = t.columns.map(col => ({
              ...col,
              description: [{
                lang: APP_LANG,
                text: annotations.columns[col.column_name] || col.description?.[0]?.text || ""
              }]
            }));
            return updatedTable;
          }
          return t;
        })
      );

      // Update column descriptions state
      const newDescriptions = { ...columnDescriptions };
      Object.entries(annotations.columns).forEach(([colName, desc]) => {
        newDescriptions[`${table.table_name}.${colName}`] = desc;
      });
      setColumnDescriptions(newDescriptions);
    } catch (error) {
      console.error('Error generating annotations:', error);
    } finally {
      setGeneratingAnnotations(prev => ({ ...prev, [table.table_name]: false }));
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);

      // Transform the connection info back to the expected format
      let connectionInfo = { ...formData.connectionInfo };
      
      if (source?.source_type === 'tabularfile') {
        // Make sure we're properly handling the tabular file case
        const fileObjects = formData.connectionInfo['Tabular Files']?.file_objects || [];
        connectionInfo = {
          file_objects: fileObjects
        };
        
        // Validate that we have at least one file
        if (!connectionInfo.file_objects || connectionInfo.file_objects.length === 0) {
          throw new Error('At least one tabular file is required');
        }
      }

      const payload = {
        source_name: formData.name,
        is_private: formData.isPrivate,
        description: [{
          lang: APP_LANG,
          text: formData.description
        }],
        connection_info: connectionInfo,
        additional_details: "",
        entities: sourceEntities
          ? sourceEntities
              .filter(table => selectedTables.has(table.table_name))
              .map(table => ({
                table_name: table.table_name,
                description: [{
                  lang: APP_LANG,
                  text: table.description?.[0]?.text || ""
                }],
                domains: table.domains || [],
                file_type: table.file_type || "",
                object_name: table.object_name || "",
                media_type: table.media_type || "",
                original_filename: table.original_filename || "",
                sheet_name: table.sheet_name || "",
                tags: table.tags || "",
                columns: table.columns.map(column => ({
                  column_name: column.column_name,
                  type: column.type,
                  description: [{
                    lang: APP_LANG,
                    text: columnDescriptions[`${table.table_name}.${column.column_name}`] || ""
                  }],
                  tags: column.tags || ""
                })),
                primary_keys: table.primary_keys || [],
                foreign_keys: table.foreign_keys || []
              }))
          : []
      };

      console.log('Sending payload:', JSON.stringify(payload));
      
      const response = await dataSourcesService.updateSource(sourceId, payload);
      console.log('Update response:', response);
      
      onUpdateSource();
      onClose();
    } catch (err) {
      console.error('Save error:', err);
      setError(err.message || 'Failed to save changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const renderSourceConfigTab = () => (
    <motion.div 
      className="tab-content"
      initial="hidden"
      animate="visible"
      variants={fadeIn}
    >
      <motion.div className="form-group" variants={slideUp} custom={0}>
        <label>
          Source Name
          <span className="required-indicator">*</span>
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          required
        />
      </motion.div>

      <motion.div className="form-group" variants={slideUp} custom={1}>
        <label>Source Type</label>
        <input
          type="text"
          value={source?.source_type || ''}
          className="disabled"
          disabled
        />
      </motion.div>

      <motion.div className="form-group" variants={slideUp} custom={2}>
        <label>Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Enter source description..."
        />
      </motion.div>

      <motion.div 
        className="connection-form"
        variants={slideUp}
        custom={3}
        whileHover={{ boxShadow: "var(--shadow-md)" }}
      >
        <h4>{source?.source_type === 'tabularfile' ? 'Tabular Files' : 'Connection Information'}</h4>
        {Object.entries(formData.connectionInfo).map(([key, value], index) => {
          if (source?.source_type === 'sqlserver') {
            return (
              <motion.div 
                className="form-group" 
                key={key}
                variants={slideRight}
                initial="hidden"
                animate="visible"
                transition={{ delay: index * 0.1 }}
              >
                <label>{key}</label>
                <input
                  type={key.toLowerCase() === 'password' ? 'password' : 'text'}
                  value={value}
                  onChange={(e) => handleConnectionInfoChange(key, e.target.value)}
                  disabled={isSaving}
                />
              </motion.div>
            );
          } else if (source?.source_type === 'tabularfile') {
            return formData.connectionInfo['Tabular Files'].file_objects.map((file, fileIndex) => {
              return (
                <motion.div 
                  key={fileIndex}
                  variants={slideRight}
                  initial="hidden"
                  animate="visible"
                  transition={{ delay: fileIndex * 0.1 }}
                  whileHover={{ x: 5 }}
                >
                  {file.original_filename}
                </motion.div>
              );
            });
          }
        })}
      </motion.div>
    </motion.div>
  );

  const renderSchemaConfigTab = () => {
    const filteredTables = sourceEntities?.filter(table =>
      table.table_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (table.description?.find(desc => desc.lang === APP_LANG)?.text || '').toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    // Ensure we're using both the selectedTables state and the _selected flag
    const selectedTablesList = filteredTables.filter(table => 
      selectedTables.has(table.table_name) || table._selected === true
    );
    const unselectedTablesList = filteredTables.filter(table => 
      !selectedTables.has(table.table_name) && table._selected !== true
    );

    return (
      <motion.div 
        className="tab-content"
        initial="hidden"
        animate="visible"
        variants={fadeIn}
      >
        <motion.div 
          className="schema-header"
          variants={slideUp}
        >
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search tables..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <motion.div 
            className="table-stats"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            {selectedTablesList.length} tables selected
          </motion.div>
        </motion.div>

        <div className="tables-section">
          <motion.h4 variants={slideUp}>Selected Tables</motion.h4>
          {selectedTablesList.length === 0 ? (
            <motion.p 
              className="empty-state"
              variants={slideUp}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              No tables selected. Select tables from the Available Tables section below.
            </motion.p>
          ) : (
            <div className="tables-grid">
              <AnimatePresence>
                {selectedTablesList.map((table, index) => (
                  <motion.div 
                    className="table-card selected" 
                    key={table.table_name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ y: -5 }}
                  >
                    <div className="table-header">
                      <h4>{table.table_name}</h4>
                      <div className="table-actions">
                        <motion.button
                          className="generate-button"
                          onClick={() => handleGenerateAnnotation(table)}
                          disabled={generatingAnnotations[table.table_name]}
                          title="Generate Annotations"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          {generatingAnnotations[table.table_name] ? (
                            <div className="button-loader" />
                          ) : (
                            'Generate Annotation'
                          )}
                        </motion.button>
                        <motion.button
                          className="remove-button"
                          onClick={() => toggleTableSelection(table.table_name)}
                          title="Remove table"
                          whileHover={{ scale: 1.1, rotate: 90 }}
                          whileTap={{ scale: 0.9 }}
                        >
                          <X size={16} />
                        </motion.button>
                        <motion.button
                          className="expand-button"
                          onClick={() => toggleTableExpansion(table.table_name)}
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                        >
                          {expandedTables[table.table_name] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </motion.button>
                      </div>
                    </div>
                    <div className="table-description">
                      <textarea
                        value={table.description?.find(desc => desc.lang === APP_LANG)?.text || ''}
                        onChange={(e) => {
                          const newDesc = table.description?.map(desc =>
                            desc.lang === APP_LANG ? { ...desc, text: e.target.value } : desc
                          ) || [{ lang: APP_LANG, text: e.target.value }];
                          const updatedTable = { ...table, description: newDesc };
                          setSourceEntities(prev =>
                            prev.map(t => t.table_name === table.table_name ? updatedTable : t)
                          );
                        }}
                        placeholder="Add table description..."
                        rows={2}
                      />
                    </div>
                    <AnimatePresence>
                      {expandedTables[table.table_name] && (
                        <motion.div 
                          className="columns-list"
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          {table.columns.map((column, colIndex) => (
                            <motion.div 
                              className="column-item" 
                              key={column.column_name}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: colIndex * 0.03 }}
                            >
                              <div className="column-info">
                                <div className="column-name">
                                  {column.column_name}
                                  {table.primary_keys?.includes(column.column_name) && (
                                    <span className="primary-key-badge">PK</span>
                                  )}
                                </div>
                                <div className="column-type">{column.type}</div>
                              </div>
                              <div className="column-description">
                                <textarea
                                  value={columnDescriptions[`${table.table_name}.${column.column_name}`] || ''}
                                  onChange={(e) => handleColumnDescriptionChange(
                                    table.table_name,
                                    column.column_name,
                                    e.target.value
                                  )}
                                  placeholder="Enter column description..."
                                />
                              </div>
                            </motion.div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}

          <motion.h4 variants={slideUp} transition={{ delay: 0.2 }}>Available Tables</motion.h4>
          {unselectedTablesList.length === 0 ? (
            <motion.p 
              className="empty-state"
              variants={slideUp}
              transition={{ delay: 0.3 }}
            >
              No additional tables available.
            </motion.p>
          ) : (
            <div className="tables-grid">
              {unselectedTablesList.map((table, index) => (
                <motion.div 
                  className="table-card" 
                  key={table.table_name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + index * 0.05 }}
                  whileHover={{ y: -5 }}
                >
                  <div className="table-header">
                    <h4>{table.table_name}</h4>
                    <motion.button
                      className="add-button"
                      onClick={() => toggleTableSelection(table.table_name)}
                      title="Add table"
                      whileHover={{ scale: 1.1, rotate: 90 }}
                      whileTap={{ scale: 0.9 }}
                    >
                      <Plus size={16} />
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    );
  };

  if (isLoading) {
    return (
      <div className="edit-source-wizard">
        <motion.div 
          className="wizard-modal"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", duration: 0.5 }}
        >
          <motion.div 
            className="loading-state"
            animate={{ 
              y: [0, -10, 0],
              transition: { 
                y: { repeat: Infinity, duration: 1.5, ease: "easeInOut" }
              }
            }}
          >
            <div className="loader" />
            <span>Loading source details...</span>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="edit-source-wizard">
      <motion.div 
        className="wizard-modal"
        ref={modalRef}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", duration: 0.5 }}
      >
        <div className="wizard-header">
          <motion.h3
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            Edit Source
          </motion.h3>
          <motion.button 
            className="close-button" 
            onClick={onClose}
            whileHover={{ rotate: 90, scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <X size={20} />
          </motion.button>
        </div>

        <div className="tabs">
          <motion.button
            className={`tab ${activeTab === TABS.CONFIGURE_SOURCE ? 'active' : ''}`}
            onClick={() => setActiveTab(TABS.CONFIGURE_SOURCE)}
            whileHover={{ y: -2 }}
            whileTap={{ y: 1 }}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Configure Source
          </motion.button>
          <motion.button
            className={`tab ${activeTab === TABS.CONFIGURE_SCHEMA ? 'active' : ''}`}
            onClick={() => setActiveTab(TABS.CONFIGURE_SCHEMA)}
            whileHover={{ y: -2 }}
            whileTap={{ y: 1 }}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Configure Schema
          </motion.button>
        </div>

        <div className="wizard-content">
          <AnimatePresence>
            {error && (
              <motion.div 
                className="error-state" 
                ref={errorRef}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0 }}
              >
                <AlertCircle size={16} />
                <p>{error}</p>
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === TABS.CONFIGURE_SOURCE
                ? renderSourceConfigTab()
                : renderSchemaConfigTab()}
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="wizard-footer">
          <motion.button 
            className="secondary-button" 
            onClick={onClose}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Cancel
          </motion.button>
          <motion.button
            className="primary-button"
            onClick={handleSave}
            disabled={isSaving}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {isSaving ? (
              <motion.div 
                animate={{ 
                  rotate: 360,
                  transition: { repeat: Infinity, duration: 1.5, ease: "linear" }
                }}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <Loader size={16} />
                Saving...
              </motion.div>
            ) : (
              'Save Changes'
            )}
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
};

export default EditSourceWizard; 