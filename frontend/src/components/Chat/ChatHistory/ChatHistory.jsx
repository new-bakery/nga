import React, { useEffect, useRef } from 'react';
import SqlResponse from '../SqlResponse/SqlResponse';
import PlotResponse from '../PlotResponse/PlotResponse';
import PythonDataResponse from '../PythonDataResponse/PythonDataResponse';
import MarkdownResponse from '../MarkdownResponse/MarkdownResponse';
import './ChatHistory.scss';

function ChatHistory({ messages, progressMessage, isLoading, isThinking }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const renderMessage = (message, isLastMessage) => {
    if (!message) return null;

    if (message.role === 'user') {
      return (
        <div className="message-section user">
          <div className="message-header">
            <div className="user-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="#6B7280" />
              </svg>
            </div>
            <span className="message-label">You</span>
          </div>
          <div className="message-content">
            <span>{message.markdowns?.length > 0 ? message.markdowns[0] : ""}</span>
            {message.image_url && (
              <div className="message-image">
                <img src={message.image_url} alt="Uploaded content" />
              </div>
            )}
          </div>
        </div>
      );
    }

    if (message.role === 'assistant') {
      return (
        <div className="message-section assistant">
          <div className="message-header">
            <div className="assistant-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="#10a37f" strokeWidth="2" />
                <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" fill="#10a37f" />
              </svg>
            </div>
            <span className="message-label">Assistant</span>
            {isLastMessage && isThinking && <img src="/ai-thinking.gif" alt="Thinking" height="32" width="32" />}
          </div>
          <div className="message-content">
            {message.agents?.map((agent, index) => (
              <div key={index} className="agent-response">
                <div className="agent-header">
                  {agent.role === 'sql-agent'  && (Array.isArray(agent.jsons) && agent.jsons.length > 0 )&& (
                    <div className="agent-icon sql-agent">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M4 5h16v2H4z" fill="#4f46e5" />
                        <path d="M4 9h16v2H4z" fill="#4f46e5" />
                        <path d="M4 13h16v2H4z" fill="#4f46e5" />
                        <path d="M4 17h10v2H4z" fill="#4f46e5" />
                      </svg>
                      <span>SQL Results</span>
                    </div>
                  )}
                  {agent.role === 'chat-agent' && (
                    <div className="agent-icon chat-agent">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="#10a37f" />
                      </svg>
                      <span>Chat Response</span>
                    </div>
                    )}
                  {agent.role === 'plotly-agent' && (
                    <div className="agent-icon plotly-agent">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 3v18h18" stroke="#1092a3" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M7 10v8" stroke="#1092a3" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M12 6v12" stroke="#1092a3" strokeWidth="2" strokeLinecap="round"/>
                        <path d="M17 12v6" stroke="#1092a3" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                      <span>Plot</span>
                    </div>
                  )}
                  {agent.role === 'python-data-agent' && (Array.isArray(agent.jsons) && agent.jsons.length > 0 ) && (
                    <div className="agent-icon python-data-agent">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M4 5h16v2H4z" fill="#a31057" />
                        <path d="M4 9h16v2H4z" fill="#a31057" />
                        <path d="M4 13h16v2H4z" fill="#a31057" />
                        <path d="M4 17h10v2H4z" fill="#a31057" />
                      </svg>
                      <span>Python Data</span>
                    </div>
                  )}
                  {agent.is_error && (
                    <div className="error-icon">
                      <img src="/error-icon.png" alt="Error" />
                    </div>
                  )}
                </div>
                {
                  agent.is_error && (
                    <div className="agent-error">
                      <MarkdownResponse markdowns={[agent.error_message]} />
                    </div>
                  )
                }
                {agent.role === 'sql-agent' && !agent.is_error  && (Array.isArray(agent.jsons) && agent.jsons.length > 0 ) && (
                  <SqlResponse response={{
                    chartData: {
                      summary: "",
                      sql: Array.isArray(agent.thought_process) ? agent.thought_process[0] : agent.thought_process || "",
                      data: agent.jsons || []
                    }
                  }} />
                )}
                {agent.role === 'chat-agent' && !agent.is_error && (
                  <MarkdownResponse markdowns={agent.markdowns || []} />
                )}
                {agent.role === 'plotly-agent' && (
                  <PlotResponse 
                    plotHTML= {Array.isArray(agent.thought_process) ? agent.thought_process[1] : agent.thought_process || ""} 
                  />
                )}
                {agent.role === 'python-data-agent' &&  (Array.isArray(agent.jsons) && agent.jsons.length > 0 ) && (
                  <PythonDataResponse 
                    data = {agent.jsons || []}
                    code = {agent.thought_process.length > 0 ? agent.thought_process[0] : ""}
                  />
                )}
              </div>
            ))}
          </div>          
          {isLastMessage && isThinking && progressMessage && (
            <div className="message-progress">
              {progressMessage}
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  const renderEmptyState = () => {
    return (
      <div className="empty-chat-state">
        <div className="empty-chat-content">
          <div className="assistant-avatar">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="#10a37f" strokeWidth="2" />
              <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" fill="#10a37f" />
            </svg>
          </div>
          <h3>How can I help you today?</h3>
          <p>Ask me anything about your data. I can help you analyze trends, create visualizations, and provide insights.</p>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-history">
      {messages?.length === 0 ? renderEmptyState() : (
        messages?.map((message, index) => (
          <div key={`message-${index}-${message.type}`} className="message-wrapper">
            {renderMessage(message, index === messages.length - 1)}
          </div>
        ))
      )}
      {isLoading && (
        <div className="message-section assistant">
          <div className="message-header">
            <div className="assistant-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="#10a37f" strokeWidth="2" />
                <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" fill="#10a37f" />
              </svg>
            </div>
            <span className="message-label">Assistant</span>
          </div>
          <div className="message-content loading-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatHistory; 