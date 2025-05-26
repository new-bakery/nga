import React, { useState } from 'react';
import ChatHistory from '../ChatHistory/ChatHistory';
import ChatInput from '../ChatInput/ChatInput';
import WarningModal from '../../common/WarningModal/WarningModal';
import './ChatInterface.scss';

function ChatInterface({ messages, isLoading, onSendMessage, onManageClick, selectedSources, progressMessage, isThinking }) {
  const [showWarning, setShowWarning] = useState(false);

  const handleSendMessage = (message, enableSOP) => {
    if (!selectedSources || selectedSources.length === 0) {
      setShowWarning(true);
      return;
    }
    onSendMessage(message, selectedSources, enableSOP);
  };

  return (
    <div className="chat-interface">
      <ChatHistory 
        messages={messages} 
        isLoading={isLoading} 
        progressMessage={progressMessage} 
        isThinking={isThinking} />
      <ChatInput
        onSendMessage={handleSendMessage}
        onManageClick={onManageClick}
        isLoading={isLoading}
      />
      <WarningModal
        isOpen={showWarning}
        onClose={() => setShowWarning(false)}
        title="Data Source Required"
        message="Please select at least one data source before sending a message. Click the manage button to select data sources."
      />
    </div>
  );
}

export default ChatInterface; 