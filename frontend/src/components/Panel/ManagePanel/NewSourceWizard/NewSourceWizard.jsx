import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Database, File, X, Upload, Check, Info, AlertCircle, Search, ChevronUp, ChevronDown, Loader } from 'react-feather';
import { useDropzone } from 'react-dropzone';
import { DATA_SOURCE_TYPES } from '../../../../constants/dataSources';
import { MOCK_SCHEMA_DATA } from '../../../../constants/mockSchemaData';
import './NewSourceWizard.scss';
import ReactFlow, { 
  Background, 
  Controls, 
  Handle, 
  Position,
  MarkerType 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { dataSourcesService } from '../../../../services/dataSources';
import debounce from 'lodash/debounce';
import { motion, AnimatePresence } from 'framer-motion';

const STEPS = {
  SELECT_TYPE: 0,
  CONFIGURE_SOURCE: 1,
  CONFIGURE_SCHEMA: 2,
  REVIEW_CONFIG: 3
};

const APP_LANG = import.meta.env.VITE_APP_LANG || 'en';

function NewSourceWizard({ selectedType, onClose, onCreateSource, initialData, isAdminContext = false }) {
  const [currentStep, setCurrentStep] = useState(STEPS.SELECT_TYPE);
  const [sourceTypes, setSourceTypes] = useState([]);
  const [sourceTypeDetails, setSourceTypeDetails] = useState(null);
  const [sourceConfig, setSourceConfig] = useState({
    type: selectedType || '',
    name: '',
    connection: {}
  });
  const [sourceName, setSourceName] = useState('');
  const [sourceNameError, setSourceNameError] = useState('');
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [isLoadingSchema, setIsLoadingSchema] = useState(false);
  const [showRelationshipInfo, setShowRelationshipInfo] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [generatingAnnotations, setGeneratingAnnotations] = useState({});
  
  // Add these state variables at the component level
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTables, setSelectedTables] = useState(new Set());
  const [expandedTables, setExpandedTables] = useState(new Set());
  const [isCreatingSource, setIsCreatingSource] = useState(false);

  // Add refs for animations
  const modalRef = useRef(null);
  
  // Animation variants for framer-motion
  const fadeIn = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.3 } }
  };
  
  const slideUp = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } }
  };

  // Create debounced search function
  const debouncedSearch = useCallback(
    debounce((value) => {
      setSearchTerm(value);
    }, 300),
    []
  );

  // Load source types on component mount
  useEffect(() => {
    const loadSourceTypes = async () => {
      try {
        const types = await dataSourcesService.getSourceTypes();
        setSourceTypes(types);
      } catch (error) {
        console.error('Error loading source types:', error);
      }
    };
    loadSourceTypes();
  }, []);

  // Load source type details when type is selected
  useEffect(() => {
    const loadSourceTypeDetails = async () => {
      if (sourceConfig.type) {
        try {
          const details = await dataSourcesService.getSourceTypeDetails(sourceConfig.type);
          setSourceTypeDetails(details);
        } catch (error) {
          console.error('Error loading source type details:', error);
        }
      }
    };
    loadSourceTypeDetails();
  }, [sourceConfig.type]);

  const onDrop = useCallback(acceptedFiles => {
    const file = acceptedFiles[0];
    setSourceConfig(prev => ({
      ...prev,
      file,
      name: file.name
    }));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  const loadSchemaData = async () => {
    setIsLoadingSchema(true);
    try {
      const response = await dataSourcesService.getSourceEntities(sourceConfig.type, sourceConfig.connection);
      if (response.data) {
        setSourceConfig(prev => ({
          ...prev,
          tables: response.data.map(table => ({
            id: table.table_name,
            name: table.table_name,
            file_type: table.file_type,
            media_type: table.media_type,
            object_name: table.object_name,
            sheet_name: table.sheet_name,
            original_file: table.original_file,
            description: table.description?.find(desc => desc.lang === APP_LANG)?.text || '',
            columns: table.columns.map(col => ({
              id: col.column_name,
              name: col.column_name,
              type: col.type,
              description: col.description?.find(desc => desc.lang === APP_LANG)?.text || '',
              isPrimaryKey: table.primary_keys?.includes(col.column_name) || false
            }))
          }))
        }));
      }
    } catch (error) {
      console.error('Error loading schema:', error);
      setSourceConfig(prev => ({
        ...prev,
        tables: [],
        schemaError: 'Failed to load schema. Please check your connection settings.'
      }));
    } finally {
      setIsLoadingSchema(false);
    }
  };

  const validateConnectionFields = () => {
    if (!sourceTypeDetails?.connection_info) return false;

    const errors = {};
    let isValid = true;

    Object.entries(sourceTypeDetails.connection_info).forEach(([fieldName, fieldInfo]) => {
      if (fieldInfo.required) {
        if (fieldInfo.file_uploader) {
          const fileObjects = sourceConfig.connection.file_objects;
          if (!fileObjects || fileObjects.length === 0) {
            errors[fieldName] = 'Please upload at least one file';
            isValid = false;
          }
        } else if (!sourceConfig.connection[fieldName]) {
          errors[fieldName] = 'This field is required';
          isValid = false;
        }
      }
    });

    setValidationErrors(errors);
    return isValid;
  };

  const handleTestConnection = async () => {
    // Validate required fields before testing connection
    if (!validateConnectionFields()) {
      return;
    }

    setIsTestingConnection(true);
    setConnectionStatus(null);
    try {
      await dataSourcesService.testSourceConnectivity(sourceConfig.type, sourceConfig.connection);
      setConnectionStatus('success');
    } catch (error) {
      console.error('Connection test failed:', error);
      setConnectionStatus('error');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleConnectionFieldChange = (fieldName, value) => {
    setSourceConfig(prev => ({
      ...prev,
      connection: {
        ...prev.connection,
        [fieldName]: value
      }
    }));
    // Clear validation error when user starts typing
    if (validationErrors[fieldName]) {
      setValidationErrors(prev => ({
        ...prev,
        [fieldName]: null
      }));
    }
  };

  const handleUpdateTable = (tableId, updates) => {
    setSourceConfig(prev => ({
      ...prev,
      tables: prev.tables.map(table => 
        table.id === tableId ? { ...table, ...updates } : table
      )
    }));
  };

  const handleRemoveTable = (tableId) => {
    setSourceConfig(prev => ({
      ...prev,
      tables: prev.tables.filter(table => table.id !== tableId)
    }));
  };

  const handleRemoveColumn = (tableId, columnId) => {
    setSourceConfig(prev => ({
      ...prev,
      tables: prev.tables.map(table => 
        table.id === tableId ? {
          ...table,
          columns: table.columns.filter(col => col.id !== columnId)
        } : table
      ),
      relationships: prev.relationships.filter(rel => 
        !(rel.from.tableId === tableId && rel.from.columnId === columnId) &&
        !(rel.to.tableId === tableId && rel.to.columnId === columnId)
      )
    }));
  };

  const handleColumnDescriptionChange = useCallback((tableId, columnId, newDescription) => {
    setSourceConfig(prev => ({
      ...prev,
      tables: prev.tables.map(table => 
        table.id === tableId ? {
          ...table,
          columns: table.columns.map(col =>
            col.id === columnId ? {
              ...col,
              description: newDescription
            } : col
          )
        } : table
      )
    }));
  }, []);

  const handleTableSelect = useCallback((tableId) => {
    setSelectedTables(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(tableId)) {
        newSelected.delete(tableId);
      } else {
        newSelected.add(tableId);
      }
      return newSelected;
    });
  }, []);

  const handleTableExpand = useCallback((tableId) => {
    setExpandedTables(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(tableId)) {
        newExpanded.delete(tableId);
      } else {
        newExpanded.add(tableId);
      }
      return newExpanded;
    });
  }, []);

  const handleSelectAllTables = useCallback((checked) => {
    if (checked) {
      const allTableIds = sourceConfig.tables?.map(table => table.id) || [];
      setSelectedTables(new Set(allTableIds));
    } else {
      setSelectedTables(new Set());
    }
  }, [sourceConfig.tables]);

  React.useEffect(() => {
    if (sourceConfig.type === 'excel' && sourceConfig.file) {
      loadSchemaData();
    }
  }, [sourceConfig.file, sourceConfig.type]);

  React.useEffect(() => {
    if (currentStep === STEPS.CONFIGURE_SCHEMA && sourceConfig.type) {
      loadSchemaData();
    }
  }, [currentStep, sourceConfig.type]);

  const handleCreateSource = async () => {
    if (!sourceName.trim()) {
      setSourceNameError('Source name is required');
      return;
    }
    setIsCreatingSource(true);
    try {
      const payload = {
        source_name: sourceName,
        is_private: !isAdminContext,
        description: [{
          lang: APP_LANG,
          text: sourceConfig.description || ""
        }],
        connection_info: sourceConfig.connection,
        additional_details: "",
        entities: sourceConfig.tables
          .filter(table => selectedTables.has(table.id))
          .map(table => ({
            table_name: table.name,
            file_type: table.file_type,
            media_type: table.media_type,
            object_name: table.object_name,
            sheet_name: table.sheet_name,
            original_file: table.original_file,
            description: [{
              lang: APP_LANG,
              text: table.description || ""
            }],
            domains: [],
            tags: "",
            columns: table.columns.map(col => ({
              column_name: col.name,
              type: col.type,
              description: [{
                lang: APP_LANG,
                text: col.description || ""
              }],
              tags: ""
            })),
            primary_keys: table.columns
              .filter(col => col.isPrimaryKey)
              .map(col => col.name),
            foreign_keys: []
          }))
      };

      await dataSourcesService.createSource(sourceConfig.type, payload);
      if (onCreateSource) {
        await onCreateSource();
      }
      onClose();
    } catch (error) {
      console.error('Error creating source:', error);
      setSourceConfig(prev => ({
        ...prev,
        error: 'Failed to create source. Please try again.'
      }));
    } finally {
      setIsCreatingSource(false);
    }
  };

  const handleGenerateAnnotation = async (table) => {
    setGeneratingAnnotations(prev => ({ ...prev, [table.id]: true }));
    try {
      const payload = {
        lang: [APP_LANG],
        source_name: sourceName || "",
        source_description: [{
          lang: APP_LANG,
          text: sourceConfig.description || ""
        }],
        entity: {
          table_name: table.name,
          description: [{
            lang: APP_LANG,
            text: table.description || ""
          }],
          domains: [],
          tags: "",
          columns: table.columns.map(col => ({
            column_name: col.name,
            type: col.type,
            description: [{
              lang: APP_LANG,
              text: col.description || ""
            }],
            tags: ""
          })),
          primary_keys: table.columns
            .filter(col => col.isPrimaryKey)
            .map(col => col.name),
          foreign_keys: []
        }
      };

      const response = await dataSourcesService.generateTableAnnotation(payload);
      const annotations = response[APP_LANG];

      // Update table and column descriptions
      setSourceConfig(prev => ({
        ...prev,
        tables: prev.tables.map(t => {
          if (t.id === table.id) {
            return {
              ...t,
              description: annotations.table_description,
              columns: t.columns.map(col => ({
                ...col,
                description: annotations.columns[col.name] || col.description
              }))
            };
          }
          return t;
        })
      }));
    } catch (error) {
      console.error('Error generating annotations:', error);
    } finally {
      setGeneratingAnnotations(prev => ({ ...prev, [table.id]: false }));
    }
  };

  const renderSchemaStep = () => {
    // Filter tables based on search term
    const filteredTables = sourceConfig.tables?.filter(table => 
      table.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (table.description?.[0]?.text || '').toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const allTablesSelected = sourceConfig.tables?.length > 0 && 
      selectedTables.size === sourceConfig.tables.length;

    return (
      <div className="step-content">
        <motion.div 
          className="schema-header"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h3>Configure Schema</h3>
          <div className="schema-actions">
            <div className="select-all-container">
              <input
                type="checkbox"
                id="select-all-tables"
                checked={allTablesSelected}
                onChange={(e) => handleSelectAllTables(e.target.checked)}
              />
              <label htmlFor="select-all-tables">Select All Tables</label>
            </div>
            <div className="search-box">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search tables..."
                onChange={(e) => debouncedSearch(e.target.value)}
              />
            </div>
            <motion.div 
              className="table-stats"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              {selectedTables.size} of {sourceConfig.tables?.length || 0} tables selected
            </motion.div>
          </div>
        </motion.div>

        <div className="schema-container">
          {isLoadingSchema ? (
            <motion.div 
              className="loading-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <span className="loader"></span>
              Loading schema...
            </motion.div>
          ) : sourceConfig.schemaError ? (
            <motion.div 
              className="error-state"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 100 }}
            >
              <AlertCircle size={20} />
              <p>{sourceConfig.schemaError}</p>
            </motion.div>
          ) : filteredTables.length === 0 ? (
            <motion.div 
              className="empty-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {searchTerm ? 'No tables match your search.' : 'No tables found in the database.'}
            </motion.div>
          ) : (
            <div className="tables-grid">
              {filteredTables.map((table, index) => (
                <motion.div 
                  key={table.id} 
                  className={`table-card ${selectedTables.has(table.id) ? 'selected' : ''}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, type: "spring", stiffness: 100 }}
                  whileHover={{ y: -5 }}
                >
                  <div className="table-header">
                    <div className="table-title">
                      <input
                        type="checkbox"
                        checked={selectedTables.has(table.id)}
                        onChange={() => handleTableSelect(table.id)}
                        id={`table-${table.id}`}
                      />
                      <label htmlFor={`table-${table.id}`}>
                        <h4>{table.name}</h4>
                      </label>
                    </div>
                    <div className="table-actions">
                      <motion.button
                        className="generate-button"
                        onClick={() => handleGenerateAnnotation(table)}
                        disabled={generatingAnnotations[table.id]}
                        title="Generate Annotations"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {generatingAnnotations[table.id] ? (
                          <div className="button-loader" />
                        ) : (
                          'Generate Annotation'
                        )}
                      </motion.button>
                      <motion.button
                        className="expand-button"
                        onClick={() => handleTableExpand(table.id)}
                        title={expandedTables.has(table.id) ? "Collapse" : "Expand"}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        {expandedTables.has(table.id) ? 
                          <ChevronUp size={16} /> : 
                          <ChevronDown size={16} />
                        }
                      </motion.button>
                    </div>
                  </div>
                  <div className="table-description">
                    <textarea
                      value={table.description || ''}
                      onChange={(e) => handleUpdateTable(table.id, { description: e.target.value })}
                      placeholder="Add table description..."
                      rows={2}
                    />
                  </div>
                  <AnimatePresence>
                    {expandedTables.has(table.id) && (
                      <motion.div 
                        className="columns-list"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        {table.columns.map((column, colIndex) => (
                          <motion.div 
                            key={column.id} 
                            className="column-item"
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: colIndex * 0.03 }}
                          >
                            <div className="column-info">
                              <span className="column-name">
                                {column.name}
                                {column.isPrimaryKey && (
                                  <span className="primary-key-badge" title="Primary Key">PK</span>
                                )}
                              </span>
                              <span className="column-type">{column.type}</span>
                            </div>
                            <div className="column-description">
                              <textarea
                                value={column.description || ''}
                                onChange={(e) => handleColumnDescriptionChange(table.id, column.id, e.target.value)}
                                placeholder="Add column description..."
                                rows={2}
                              />
                            </div>
                          </motion.div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderConnectionForm = () => {
    if (!sourceTypeDetails?.connection_info) return null;

    return (
      <div className="connection-form">
        {Object.entries(sourceTypeDetails.connection_info).map(([fieldName, fieldInfo]) => {
          const value = sourceConfig.connection[fieldName] || fieldInfo.default || '';
          const error = validationErrors[fieldName];
          
          if (fieldInfo.file_uploader) {
            return (
              <div key={fieldName} className={`form-group ${error ? 'has-error' : ''}`}>
                <div className="label-with-info">
                  <label>{fieldInfo.title || fieldName}</label>
                  {fieldInfo.hint && (
                    <div className="info-tooltip">
                      <Info size={16} />
                      <span className="tooltip-text">{fieldInfo.hint}</span>
                    </div>
                  )}
                  {fieldInfo.required && <span className="required-indicator">*</span>}
                </div>
                <FileUploader 
                  fieldInfo={fieldInfo}
                  onFilesUploaded={(fileObjects) => {
                    handleConnectionFieldChange('file_objects', fileObjects);
                  }}
                />
                {error && (
                  <div className="error-message">
                    <AlertCircle size={14} />
                    <span>{error}</span>
                  </div>
                )}
              </div>
            );
          }

          // Render select for fields with allowed values
          if (fieldInfo.allowed) {
            return (
              <div key={fieldName} className={`form-group ${error ? 'has-error' : ''}`}>
                <div className="label-with-info">
                  <label>{fieldName}</label>
                  {fieldInfo.hint && (
                    <div className="info-tooltip">
                      <Info size={16} />
                      <span className="tooltip-text">{fieldInfo.hint}</span>
                    </div>
                  )}
                  {fieldInfo.required && <span className="required-indicator">*</span>}
                </div>
                <select
                  value={value}
                  onChange={(e) => handleConnectionFieldChange(fieldName, e.target.value)}
                  required={fieldInfo.required}
                  className={error ? 'error' : ''}
                >
                  <option value="">Select {fieldName}</option>
                  {fieldInfo.allowed.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
                {error && (
                  <div className="error-message">
                    <AlertCircle size={14} />
                    <span>{error}</span>
                  </div>
                )}
              </div>
            );
          }

          // Render input for other fields
          return (
            <div key={fieldName} className={`form-group ${error ? 'has-error' : ''}`}>
              <div className="label-with-info">
                <label>{fieldName}</label>
                {fieldInfo.hint && (
                  <div className="info-tooltip">
                    <Info size={16} />
                    <span className="tooltip-text">{fieldInfo.hint}</span>
                  </div>
                )}
                {fieldInfo.required && <span className="required-indicator">*</span>}
              </div>
              <input
                type={fieldName === 'password' ? 'password' : 'text'}
                value={value}
                onChange={(e) => handleConnectionFieldChange(fieldName, e.target.value)}
                placeholder={fieldInfo.hint}
                required={fieldInfo.required}
                className={error ? 'error' : ''}
              />
              {error && (
                <div className="error-message">
                  <AlertCircle size={14} />
                  <span>{error}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderReviewStep = () => {
    const selectedTablesList = Array.from(selectedTables);
    const selectedTablesData = sourceConfig.tables?.filter(table => 
      selectedTables.has(table.id)
    ) || [];

    return (
      <div className="step-content">
        <motion.div 
          className="review-header"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3>Review Configuration</h3>
        </motion.div>
        <motion.div 
          className="review-form"
          variants={fadeIn}
          initial="hidden"
          animate="visible"
        >
          <motion.div 
            className="form-group"
            variants={slideUp}
            initial="hidden"
            animate="visible"
          >
            <label htmlFor="source-name">Source Name<span className="required-indicator">*</span></label>
            <input
              id="source-name"
              type="text"
              value={sourceName}
              onChange={(e) => {
                setSourceName(e.target.value);
                if (sourceNameError) setSourceNameError('');
              }}
              className={sourceNameError ? 'error' : ''}
              placeholder="Enter source name"
              disabled={isCreatingSource}
            />
            {sourceNameError && (
              <motion.div 
                className="error-message"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ duration: 0.2 }}
              >
                <AlertCircle size={14} />
                <span>{sourceNameError}</span>
              </motion.div>
            )}
          </motion.div>

          <motion.div 
            className="form-group"
            variants={slideUp}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.1 }}
          >
            <label htmlFor="source-description">Description</label>
            <textarea
              id="source-description"
              value={sourceConfig.description}
              onChange={(e) => setSourceConfig(prev => ({
                ...prev,
                description: e.target.value
              }))}
              placeholder="Enter source description"
              disabled={isCreatingSource}
            />
          </motion.div>
          
          <motion.div 
            className="selected-tables-section"
            variants={slideUp}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.2 }}
          >
            <h4>Selected Tables ({selectedTablesList.length})</h4>
            <div className="selected-tables-list">
              {selectedTablesData.map((table, index) => (
                <motion.div 
                  key={table.id} 
                  className="selected-table-item"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ x: 5 }}
                >
                  <div className="table-info">
                    <span className="table-name">{table.name}</span>
                    <span className="column-count">
                      {table.columns.length} columns
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    );
  };

  const renderStepContent = () => {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          {(() => {
            switch (currentStep) {
              case STEPS.SELECT_TYPE:
                return (
                  <div className="step-content">
                    <motion.h3 
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      Select Data Source Type
                    </motion.h3>
                    <div className="source-type-grid">
                      {sourceTypes.map((type, index) => (
                        <motion.button
                          key={type.name}
                          className={`source-type-card ${sourceConfig.type === type.name ? 'selected' : ''}`}
                          onClick={() => setSourceConfig(prev => ({ 
                            ...prev, 
                            type: type.name,
                            connection: {} // Reset connection when changing type
                          }))}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <img 
                            src={`/source-icons/${type.display_info.icon}`} 
                            alt={type.display_info.display_name}
                            className="source-type-icon"
                          />
                          <span>{type.display_info.display_name}</span>
                        </motion.button>
                      ))}
                    </div>
                  </div>
                );

              case STEPS.CONFIGURE_SOURCE:
                return (
                  <div className="step-content">
                    <motion.h3 
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      Configure Connection
                    </motion.h3>
                    {renderConnectionForm()}
                    <motion.button 
                      className="test-connection-button"
                      onClick={handleTestConnection}
                      disabled={isTestingConnection}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      {isTestingConnection ? (
                        <span>Testing...</span>
                      ) : connectionStatus === 'success' ? (
                        <><Check size={16} /> Connected</>
                      ) : connectionStatus === 'error' ? (
                        'Connection Failed'
                      ) : (
                        'Test Connection'
                      )}
                    </motion.button>
                  </div>
                );

              case STEPS.CONFIGURE_SCHEMA:
                return renderSchemaStep();

              case STEPS.REVIEW_CONFIG:
                return renderReviewStep();

              default:
                return null;
            }
          })()}
        </motion.div>
      </AnimatePresence>
    );
  };

  const handleNextStep = async () => {
    if (currentStep === STEPS.REVIEW_CONFIG) {
      await handleCreateSource();
    } else if (currentStep < 3) {
      if (currentStep === STEPS.CONFIGURE_SOURCE && sourceConfig.type) {
        if (sourceConfig.type === 'excel' && !sourceConfig.file) {
          alert('Please upload an Excel file first');
          return;
        }
        if (sourceConfig.type !== 'excel' && !connectionStatus) {
          alert('Please test the connection first');
          return;
        }
      }
      setCurrentStep(currentStep + 1);
    }
  };

  return (
    <div className="new-source-wizard">
      <motion.div 
        className="wizard-modal"
        ref={modalRef}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", duration: 0.5 }}
      >
        <div className="wizard-header">
          <div className="steps-indicator">
            {Object.values(STEPS).map(step => (
              <motion.div
                key={step}
                className={`step-indicator ${currentStep === step ? 'active' : ''} 
                  ${currentStep > step ? 'completed' : ''}`}
                whileHover={{ scale: 1.1 }}
                animate={currentStep === step ? { scale: [1, 1.1, 1] } : {}}
                transition={{ duration: 0.5 }}
              >
                {step + 1}
              </motion.div>
            ))}
          </div>
          <motion.button 
            className="close-button" 
            onClick={onClose}
            whileHover={{ rotate: 90, scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <X size={20} />
          </motion.button>
        </div>

        <div className="wizard-content">
          {renderStepContent()}
        </div>

        <div className="wizard-footer">
          <motion.button
            className="secondary-button"
            onClick={() => currentStep > 0 && setCurrentStep(currentStep - 1)}
            disabled={currentStep === 0}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Back
          </motion.button>
          <motion.button
            className="primary-button"
            onClick={handleNextStep}
            disabled={
              (currentStep === STEPS.SELECT_TYPE && !sourceConfig.type) ||
              (currentStep === STEPS.CONFIGURE_SCHEMA && selectedTables.size === 0) ||
              (currentStep === STEPS.REVIEW_CONFIG && isCreatingSource)
            }
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {currentStep === STEPS.REVIEW_CONFIG ? (
              isCreatingSource ? (
                <>
                  <span className="button-loader"></span>
                  Creating...
                </>
              ) : (
                'Create'
              )
            ) : (
              'Next'
            )}
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}

const TableNode = ({ data }) => {
  return (
    <div className="table-node">
      <div className="table-node-header">
        <span>{data.label}</span>
      </div>
      <div className="table-node-columns">
        {data.columns.map(column => (
          <div key={column.id} className="table-node-column">
            <Handle
              type="source"
              position={Position.Right}
              id={column.id}
              className="column-handle"
            />
            <Handle
              type="target"
              position={Position.Left}
              id={column.id}
              className="column-handle"
            />
            <span className="column-name">{column.name}</span>
            <span className="column-type">{column.type}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const FileUploader = ({ fieldInfo, onFilesUploaded, disabled = false }) => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFileObjects, setUploadedFileObjects] = useState([]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: acceptedFiles => {
      if (!fieldInfo.multiple && uploadedFiles.length > 0) {
        setUploadedFiles([...acceptedFiles.slice(0, 1)]);
      } else {
        setUploadedFiles(prev => [...prev, ...acceptedFiles]);
      }
    },
    accept: fieldInfo.allowed_exts.reduce((acc, ext) => {
      if (ext === '.xlsx') {
        acc['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = ['.xlsx'];
      } else if (ext === '.csv') {
        acc['text/csv'] = ['.csv'];
      }
      return acc;
    }, {}),
    multiple: fieldInfo.multiple,
    disabled: disabled || isUploading
  });

  const handleUpload = async () => {
    setIsUploading(true);
    setUploadError(null);
    const newUploadedObjects = [];

    try {
      for (const file of uploadedFiles) {
        const result = await dataSourcesService.uploadFile(file);
        newUploadedObjects.push({
          object_name: result.object_name,
          media_type: file.type,
          original_filename: file.name
        });
      }

      setUploadedFileObjects(prev => [...prev, ...newUploadedObjects]);
      onFilesUploaded([...uploadedFileObjects, ...newUploadedObjects]);
      setUploadedFiles([]);
    } catch (error) {
      setUploadError(error.message || 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  };

  const removeUploadedFile = (index) => {
    setUploadedFileObjects(prev => {
      const newFiles = prev.filter((_, i) => i !== index);
      onFilesUploaded(newFiles);
      return newFiles;
    });
  };

  const removeSelectedFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="file-uploader">
      <motion.div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''}`}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <input {...getInputProps()} />
        <motion.div 
          initial={{ y: 0 }}
          animate={{ y: isDragActive ? -10 : 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
          <Upload size={24} />
        </motion.div>
        <p>Drag & drop files here, or click to select files</p>
        <small>Allowed: {fieldInfo.allowed_exts.join(', ')}</small>
      </motion.div>

      <AnimatePresence>
        {uploadedFileObjects.length > 0 && (
          <motion.div 
            className="uploaded-files-list"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <h4>Uploaded Files:</h4>
            {uploadedFileObjects.map((file, index) => (
              <motion.div 
                key={index} 
                className="file-item uploaded"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="file-info">
                  <span className="file-name">{file.original_filename}</span>
                  <span className="file-status">
                    <Check size={14} />
                    Uploaded
                  </span>
                </div>
                <motion.button 
                  className="remove-button"
                  onClick={() => removeUploadedFile(index)}
                  disabled={disabled}
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X size={16} />
                </motion.button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {uploadedFiles.length > 0 && (
          <motion.div 
            className="selected-files-list"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <h4>Selected Files:</h4>
            {uploadedFiles.map((file, index) => (
              <motion.div 
                key={index} 
                className="file-item pending"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="file-info">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
                <motion.button 
                  className="remove-button"
                  onClick={() => removeSelectedFile(index)}
                  disabled={isUploading}
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X size={16} />
                </motion.button>
              </motion.div>
            ))}
            <motion.button 
              className="upload-button"
              onClick={handleUpload}
              disabled={isUploading || disabled}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
            >
              {isUploading ? (
                <>
                  <Loader className="spin" size={14} />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload size={14} />
                  Upload Files
                </>
              )}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {uploadError && (
        <motion.div 
          className="error-message"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring" }}
        >
          <AlertCircle size={16} />
          <span>{uploadError}</span>
        </motion.div>
      )}
    </div>
  );
};

export default NewSourceWizard; 