import React, { useEffect } from 'react';
import './WarningModal.scss';

function WarningModal({ isOpen, onClose, title, message }) {
  // Handle escape key press to close modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (isOpen && event.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleEscKey);
    
    // When modal opens, prevent body scrolling
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      window.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'visible';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Handle click outside to close
  const handleOverlayClick = (e) => {
    if (e.target.className === 'modal-overlay') {
      onClose();
    }
  };

  return (
    <div className="warning-modal-container">
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>{title}</h3>
            <button className="close-button" onClick={onClose} aria-label="Close modal">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
          <div className="modal-body">
            <div className="warning-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="#f59e0b" strokeWidth="2"/>
                <path d="M12 8v4m0 4h.01" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="12" cy="12" r="9" fill="#f59e0b" fillOpacity="0.2" />
              </svg>
            </div>
            <p>{message}</p>
          </div>
          <div className="modal-footer">
            <button className="primary-button" onClick={onClose}>
              Got it
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WarningModal; 