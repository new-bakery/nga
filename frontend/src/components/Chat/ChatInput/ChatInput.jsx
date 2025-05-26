import React, { useState, useRef } from 'react';
import './ChatInput.scss';

function ChatInput({ onSendMessage, onManageClick }) {
  const [message, setMessage] = useState('');
  const [enableSOP, setEnableSOP] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const textareaRef = useRef(null);
  const settingsRef = useRef(null);

  // Close settings panel when clicking outside
  React.useEffect(() => {
    function handleClickOutside(event) {
      if (settingsRef.current && !settingsRef.current.contains(event.target)) {
        setShowSettings(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message, enableSOP);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    setMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        <form className="chat-input" onSubmit={handleSubmit}>
          <div className="input-buttons">
            <div className="settings-container">
              <button 
                type="button"
                className="icon-button settings-button"
                onClick={() => setShowSettings(!showSettings)}
                title="Settings"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              
              {showSettings && (
                <div className="settings-panel" ref={settingsRef}>
                  <div className="settings-item">
                    <label className="sop-toggle">
                      <span className="toggle-label">Enable SOP</span>
                      <input
                        type="checkbox"
                        checked={enableSOP}
                        onChange={(e) => setEnableSOP(e.target.checked)}
                      />
                      <span className="toggle-slider"></span>
                    </label>
                  </div>
                  <div className="settings-item">
                  <label className="sop-toggle">
                    <span className="toggle-label">Configure Data Sources</span>
                      <button 
                        type="button" 
                        className="source-button"
                        onClick={() => {
                          onManageClick();
                          setShowSettings(false);
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M4 7a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V7z" stroke="currentColor" strokeWidth="2"/>
                          <path d="M4 15a2 2 0 012-2h12a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2z" stroke="currentColor" strokeWidth="2"/>
                        </svg>
                      </button>
                    </label>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            className="message-input"
            rows={1}
            placeholder={'Message ' + import.meta.env.VITE_APP_NAME}
          />
          
          <button 
            type="submit" 
            className="send-button" 
            disabled={!message.trim()}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 12l-16-6v5l8 1-8 1v5l16-6z" fill="currentColor"/>
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatInput; 