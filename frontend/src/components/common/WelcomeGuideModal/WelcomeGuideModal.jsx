import React from 'react';
import './WelcomeGuideModal.scss';

function WelcomeGuideModal({ isOpen, onClose, onManageClick }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content welcome-guide">
        <div className="modal-header">
          <h3>Welcome to Your New Chat</h3>
          <button className="close-button" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
        <div className="modal-body">
          <div className="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#10a37f"/>
            </svg>
          </div>
          <p>Before we start, please select the data sources you'd like to analyze. This will help me provide more accurate and relevant responses.</p>
        </div>
        <div className="modal-footer">
          <button className="secondary-button" onClick={onClose}>
            Later
          </button>
          <button className="primary-button" onClick={() => { onManageClick(); onClose(); }}>
            Select Sources
          </button>
        </div>
      </div>
    </div>
  );
}

export default WelcomeGuideModal; 