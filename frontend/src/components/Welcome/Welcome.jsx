import React from 'react';
import { MessageSquare, PlusCircle, Database, BarChart2 } from 'react-feather';
import './Welcome.scss';

function Welcome() {
  return (
    <div className="welcome-container">
      <div className="welcome-content">
        <h1>Welcome to {import.meta.env.VITE_APP_NAME}</h1>
        <p className="welcome-subtitle">Your AI-powered data analysis assistant</p>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <MessageSquare size={24} />
            </div>
            <h3>Natural Conversations</h3>
            <p>Ask questions about your data in plain English. Our AI understands your intent and provides relevant insights.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <BarChart2 size={24} />
            </div>
            <h3>Visual Analytics</h3>
            <p>Get instant visualizations that help you understand trends, patterns, and insights in your data.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <Database size={24} />
            </div>
            <h3>Multiple Data Sources</h3>
            <p>Connect and analyze data from various sources including databases, spreadsheets, and APIs.</p>
          </div>
        </div>

        <div className="getting-started">
          <h2>Getting Started</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h4>Start a New Chat</h4>
                <p>Click the <PlusCircle size={16} className="inline-icon"/> New Chat button in the sidebar to begin a new analysis session.</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h4>Ask Questions</h4>
                <p>Type your questions about the data in natural language. For example: "Show me sales trends by region"</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h4>Explore Insights</h4>
                <p>View the generated visualizations and insights. You can ask follow-up questions to dive deeper.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Welcome; 