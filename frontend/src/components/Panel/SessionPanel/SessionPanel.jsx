import React from 'react';
import './SessionPanel.scss';
import Modal from '../../Modal/Modal';

function SessionPanel({ sessions = [], activeSessionId, onNewSession, onSelectSession, onDeleteSession, isCollapsed, onToggleCollapse }) {
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [sessionToDelete, setSessionToDelete] = React.useState(null);

  const getPreviewText = (session) => {
    return session.topic || 'New Conversation';
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleDeleteClick = (e, sessionId) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setIsModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (sessionToDelete) {
      onDeleteSession(sessionToDelete);
      if (sessionToDelete === activeSessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionToDelete);
        if (remainingSessions.length > 0) {
          onSelectSession(remainingSessions[0].id);
        } else {
          onSelectSession(null);
        }
      }
      setSessionToDelete(null);
    }
    setIsModalOpen(false);
  };

  return (
    <div className={`session-panel ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="session-panel-header">
        {!isCollapsed && (
          <button className="new-chat-button" onClick={onNewSession}>
            <span>+</span> New Chat
          </button>
        )}
        <button 
          className="collapse-button" 
          onClick={onToggleCollapse}
          title={isCollapsed ? "Expand panel" : "Collapse panel"}
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>
      
      {!isCollapsed && (
        <div className="sessions-list">
          {sessions.length === 0 ? (
            <div className="no-sessions">No conversations yet</div>
          ) : (
            sessions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).map((session) => (
              <div
                key={session.id}
                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                onClick={() => onSelectSession(session.id)}
                title={getPreviewText(session)}
              >
                <div className="session-item-content">
                  <div className="session-preview">
                    {getPreviewText(session)}
                  </div>
                  <div className="session-date">
                    {formatDateTime(session.timestamp)}
                  </div>
                </div>
                <button
                  className="delete-session-button"
                  onClick={(e) => handleDeleteClick(e, session.id)}
                  title="Delete conversation"
                  aria-label="Delete conversation"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation?"
      />
    </div>
  );
}

export default SessionPanel; 