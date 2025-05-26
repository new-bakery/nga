import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import './PythonDataResponse.scss';

// Register Python language for syntax highlighting
SyntaxHighlighter.registerLanguage('python', python);

function PythonDataResponse({ data, code }) {
  const [activeTab, setActiveTab] = useState('data');

  return (
    <div className="python-data-response">
      <div className="response-content">
        <div className="tab-navigation">
          <div className="tab-buttons">
            <button 
              className={`tab-button ${activeTab === 'data' ? 'active' : ''}`}
              onClick={() => setActiveTab('data')}
            >
              Data
            </button>
            <button 
              className={`tab-button ${activeTab === 'code' ? 'active' : ''}`}
              onClick={() => setActiveTab('code')}
            >
              Code
            </button>
          </div>
        </div>

        {activeTab === 'data' && data && (
          <div className="data-container">
            <div className="table-header">
              <div className="table-info">
                <span className="table-title">Result</span>
                <span className="table-count">
                  {data.length} records
                </span>
              </div>
              <button 
                className="copy-button"
                onClick={() => {
                  if (data.length > 0) {
                    const headers = Object.keys(data[0]);
                    const csvContent = [
                      headers.join(','),
                      ...data.map(row => headers.map(header => row[header]).join(','))
                    ].join('\n');
                    navigator.clipboard.writeText(csvContent);
                  }
                }}
                title="Copy as CSV"
              >
                <svg 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path 
                    d="M8 4v12h12V4H8zm11 11H9V5h10v10zm-3-14H4v12h2V3h10V1z" 
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    {data.length > 0 && Object.keys(data[0]).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).map((value, valueIndex) => (
                        <td key={valueIndex}>
                          {value?.toLocaleString?.() ?? value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'code' && code && (
          <div className="code-container">
            <div className="code-header">
              <span className="code-title">Python Code</span>
              <button 
                className="copy-button"
                onClick={() => {
                  navigator.clipboard.writeText(code);
                }}
                title="Copy Code"
              >
                <svg 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path 
                    d="M8 4v12h12V4H8zm11 11H9V5h10v10zm-3-14H4v12h2V3h10V1z" 
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
            <div className="markdown-container">
              <ReactMarkdown
                components={{
                  code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        language={match[1]}
                        style={docco}
                        customStyle={{
                          backgroundColor: '#f8f9fa',
                          padding: '1rem',
                          borderRadius: '0.5rem',
                          fontSize: '0.9rem',
                          lineHeight: '1.5'
                        }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {`\`\`\`python\n${code}\n\`\`\``}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PythonDataResponse; 