import React, { useState, useEffect } from 'react';
import { useNavigate, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';
import { Users, Database, FileText, ChevronRight } from 'react-feather';
import Header from '../../components/common/Header/Header';
import UserManagement from './UserManagement/UserManagement';
import DataSourceManagement from './DataSourceManagement/DataSourceManagement';
import SOPManagement from './SOPManagement/SOPManagement';
import './Admin.scss';

function Admin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('');
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Animation on first load
    setIsLoaded(true);
    
    // Set the active tab based on the current path
    const path = location.pathname;
    if (path.includes('/admin/users')) {
      setActiveTab('users');
    } else if (path.includes('/admin/sops')) {
      setActiveTab('sops');
    } else if (path.includes('/admin/datasources')) {
      setActiveTab('datasources');
    }
  }, [location.pathname]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    navigate(`/admin/${tab}`);
  };

  // Tab configuration with icons
  const tabConfig = [
    { id: 'users', label: 'User Management', icon: <Users size={18} /> },
    { id: 'datasources', label: 'Data Source Management', icon: <Database size={18} /> },
    { id: 'sops', label: 'SOP Management', icon: <FileText size={18} /> },
  ];

  return (
    <div className={`admin-container ${isLoaded ? 'loaded' : ''}`}>
      <Header />
      <div className="admin-content">
        <div className="admin-sidebar">
          {tabConfig.map(tab => (
            <button 
              key={tab.id}
              className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => handleTabChange(tab.id)}
            >
              {tab.icon}
              <span style={{ marginLeft: '10px' }}>{tab.label}</span>
              {activeTab === tab.id && <ChevronRight size={18} style={{ marginLeft: 'auto' }} />}
            </button>
          ))}
        </div>
        
        <div className="admin-main">
          <TransitionGroup>
            <CSSTransition
              key={location.pathname}
              classNames="route-transition"
              timeout={300}
            >
              <Routes location={location}>
                <Route path="/" element={<Navigate to="/admin/users" replace />} />
                <Route path="/users" element={<UserManagement />} />
                <Route path="/datasources" element={<DataSourceManagement />} />
                <Route path="/sops" element={<SOPManagement />} />
              </Routes>
            </CSSTransition>
          </TransitionGroup>
        </div>
      </div>
    </div>
  );
}

export default Admin; 