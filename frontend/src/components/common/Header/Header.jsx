import React, { useState, useRef, useEffect } from 'react';
import { Settings, Home, User, LogOut, ChevronDown } from 'react-feather';
import { useNavigate } from 'react-router-dom';
import authService from '../../../services/auth';
import './Header.scss';

function Header() {
  const navigate = useNavigate();
  const isAdmin = authService.isAdmin();
  const isAdminPage = window.location.pathname.startsWith('/admin');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const handleLogout = () => {
    authService.logout();
    navigate('/login', { replace: true });
  };

  const handleNavToggle = () => {
    if (isAdminPage) {
      navigate('/home');
    } else {
      navigate('/admin');
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header className="main-header">
      <div className="header-content">
        <div className="header-left">
          {/* <img 
            src="/android-chrome-192x192.png" 
            alt="App Logo" 
            className="app-logo"
            onClick={() => navigate('/home')}
            style={{ cursor: 'pointer' }}
          /> */}
          <span>{import.meta.env.VITE_APP_NAME}</span>  
        </div>

        <div className="header-right">
          <div 
            className="user-profile-container"
            ref={dropdownRef}
          >
            <div 
              className="user-profile" 
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <div className="user-avatar">
                <User size={18} />
              </div>
              <span className="user-name">
                {localStorage.getItem('username') || 'Admin'}
              </span>
              <ChevronDown 
                size={16} 
                className={`dropdown-icon ${showDropdown ? 'rotate' : ''}`} 
              />
            </div>
            
            {showDropdown && (
              <div className="user-dropdown">
                <div className="dropdown-arrow"></div>
                <div className="dropdown-content">
                  {isAdmin && (
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNavToggle();
                        setShowDropdown(false);
                      }}
                      className="dropdown-item"
                      title={isAdminPage ? "Back to Home" : "Admin Settings"}
                    >
                      {isAdminPage ? 
                        <><Home size={16} /><span>Home</span></> : 
                        <><Settings size={16} /><span>Admin</span></>}
                    </button>
                  )}
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLogout();
                    }}
                    className="dropdown-item"
                  >
                    <LogOut size={16} />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header; 