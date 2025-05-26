import React, { useState, useEffect, useRef } from 'react';
import { sopService } from '../../../services/sop';
import SOPForm from './SOPForm';
import './SOPManagement.scss';
import Modal from '../../../components/Modal/Modal';

function SOPManagement() {
  // 状态管理
  const [sops, setSOPs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedSOP, setSelectedSOP] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loadingSOPDetail, setLoadingSOPDetail] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [sopToDelete, setSopToDelete] = useState(null);
  const [error, setError] = useState(null);
  const [fadeIn, setFadeIn] = useState(false);
  
  // 使用ref来跟踪状态和定时器，避免重复请求
  const isFirstRenderRef = useRef(true);
  const searchTimeoutRef = useRef(null);
  const isSearching = useRef(false);
  const lastSearchRef = useRef(''); // 跟踪最后一次搜索参数
  const justInitializedRef = useRef(false); // 标记刚刚完成初始化
  
  // 数据加载函数
  const loadSOPs = async (searchValue = '', source = 'unknown') => {
    // 检查是否与上次搜索参数相同
    if (searchValue === lastSearchRef.current && source === 'search-debounced') {
      return;
    }
    
    if (isSearching.current) {
      return;
    }
    
    try {
      isSearching.current = true;
      setLoading(true);
      
      // 更新最后搜索参数
      lastSearchRef.current = searchValue;
      
      const data = await sopService.getAllSOPs(searchValue);
      setSOPs(data);
      
      if (!initialized) {
        setInitialized(true);
        justInitializedRef.current = true; // 标记刚刚完成初始化
        setTimeout(() => setFadeIn(true), 50);
      }
    } catch (error) {
      console.error('Failed to load SOPs:', error);
      setError('Failed to load SOPs. Please try again.');
      
      if (!initialized) {
        setInitialized(true);
        justInitializedRef.current = true; // 标记刚刚完成初始化
        setTimeout(() => setFadeIn(true), 50);
      }
    } finally {
      setLoading(false);
      isSearching.current = false;
    }
  };

  // 追踪组件挂载状态
  const isMountedRef = useRef(false);

  useEffect(() => {
    // 标记组件挂载
    if (!isMountedRef.current) {
      isMountedRef.current = true;
      document.body.classList.add('loading-sop');
    }
    
    // 清理函数
    return () => {
      document.body.classList.remove('loading-sop');
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // 处理数据加载和搜索
  useEffect(() => {
    // 只在首次渲染时加载数据
    if (isFirstRenderRef.current) {
      isFirstRenderRef.current = false;
      loadSOPs('', 'initial-mount');
      return; // 首次加载提前返回，避免设置搜索超时
    }
    
    // 如果刚刚完成初始化，重置标记并跳过搜索
    if (justInitializedRef.current) {
      justInitializedRef.current = false;
      return;
    }
    
    // 初始化完成后，处理搜索逻辑
    if (initialized) {
      // 清除任何现有的定时器
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
      
      // 设置新的搜索定时器
      searchTimeoutRef.current = setTimeout(() => {
        if (!isSearching.current) {
          loadSOPs(searchTerm, 'search-debounced');
        }
      }, 500);
    }
  }, [searchTerm, initialized]);

  // 事件处理函数
  const handleCreate = () => {
    setSelectedSOP(null);
    setShowModal(true);
  };

  const handleEdit = async (sop) => {
    try {
      setLoadingSOPDetail(true);
      const sopDetail = await sopService.getSOP(sop.id);
      setSelectedSOP(sopDetail);
      setShowModal(true);
    } catch (error) {
      console.error('Failed to load SOP detail:', error);
      setError('Failed to load SOP details. Please try again.');
    } finally {
      setLoadingSOPDetail(false);
    }
  };

  const handleDeleteClick = (sop) => {
    setSopToDelete(sop);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await sopService.deleteSOP(sopToDelete.id);
      loadSOPs(searchTerm, 'after-delete');
      setShowDeleteConfirm(false);
      setSopToDelete(null);
    } catch (error) {
      console.error('Failed to delete SOP:', error);
      setError('Failed to delete SOP. Please try again.');
    }
  };

  const handleSave = async (sopData) => {
    try {
      if (selectedSOP) {
        await sopService.updateSOP(selectedSOP.id, sopData);
      } else {
        await sopService.createSOP(sopData);
      }
      setShowModal(false);
      loadSOPs(searchTerm, 'after-save');
    } catch (error) {
      console.error('Failed to save SOP:', error);
      setError('Failed to save SOP. Please try again.');
    }
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  // 条件渲染 - 初始加载状态
  if (!initialized) {
    return (
      <div className="sop-management-wrapper">
        <div className="sop-management initial-loading">
          <div className="loading-container">
            <div className="spinner"></div>
            <span>Loading SOPs...</span>
          </div>
        </div>
      </div>
    );
  }

  // 主要渲染
  return (
    <div className="sop-management-wrapper">
      <div className={`sop-management ${fadeIn ? 'fade-in' : ''}`}>
        <div className="sop-management-header">
          <h2>SOP Management</h2>
          <div className="sop-management-actions">
            <input
              type="text"
              placeholder="Search SOPs..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="search-input"
            />
            <button onClick={handleCreate} className="create-button">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Create New SOP
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="close-error">
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        )}

        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <span>Loading SOPs...</span>
          </div>
        ) : sops.length === 0 ? (
          <div className="no-data">No SOPs found. Create a new one to get started.</div>
        ) : (
          <div className="sop-list">
            {sops.map((sop) => (
              <div key={sop.id} className="sop-item">
                <div className="sop-info">
                  <h3>{sop.title}</h3>
                  <p>{sop.description}</p>
                </div>
                <div className="sop-actions">
                  <button 
                    onClick={() => handleEdit(sop)} 
                    className="edit-button"
                    disabled={loadingSOPDetail}
                    title="Edit SOP"
                  >
                    {loadingSOPDetail && sop.id === selectedSOP?.id ? (
                      <div className="button-spinner"></div>
                    ) : (
                      <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                      </svg>
                    )}
                  </button>
                  <button 
                    onClick={() => handleDeleteClick(sop)} 
                    className="delete-button"
                    disabled={loadingSOPDetail}
                    title="Delete SOP"
                  >
                    <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      <line x1="10" y1="11" x2="10" y2="17"></line>
                      <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {showModal && (
          <SOPForm
            sop={selectedSOP}
            onSave={handleSave}
            onClose={() => setShowModal(false)}
          />
        )}

        <Modal
          isOpen={showDeleteConfirm}
          onClose={() => {
            setShowDeleteConfirm(false);
            setSopToDelete(null);
          }}
          onConfirm={handleDeleteConfirm}
          title="Delete SOP"
          message={`Are you sure you want to delete "${sopToDelete?.title}"? This action cannot be undone.`}
        />
      </div>
    </div>
  );
}

export default SOPManagement;