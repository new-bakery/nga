import React, { useState, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { toPng } from 'html-to-image';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import sql from 'react-syntax-highlighter/dist/esm/languages/hljs/sql';
import './SqlResponse.scss';

// Register SQL language for syntax highlighting
SyntaxHighlighter.registerLanguage('sql', sql);

function ChartResponse({ response }) {
  const [activeTab, setActiveTab] = useState('data');
  const [chartType, setChartType] = useState('grouped');
  const chartRef = useRef(null);

  const { summary, sql: sqlQuery, data } = response.chartData;

  // Transform data for the chart
  /*const transformedData = data.reduce((acc, curr) => {
    const countryData = acc.find(item => item.country === curr.country);
    if (countryData) {
      countryData[curr.product] = curr.value;
    } else {
      const newCountryData = { country: curr.country };
      newCountryData[curr.product] = curr.value;
      acc.push(newCountryData);
    }
    return acc;
  }, []);

  // Get unique products for chart series
  const products = [...new Set(data.map(item => item.product))];

  // Define chart colors
  const colors = ['#8b5cf6', '#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa'];*/

  const handleDownload = async () => {
    if (chartRef.current) {
      try {
        const dataUrl = await toPng(chartRef.current, {
          quality: 1.0,
          backgroundColor: 'white',
        });
        
        // Create download link
        const link = document.createElement('a');
        link.download = 'chart-analysis.png';
        link.href = dataUrl;
        link.click();
      } catch (err) {
        console.error('Error downloading chart:', err);
      }
    }
  };

  const renderChart = () => {
    return (
      <div ref={chartRef} style={{ width: '100%', height: 400, backgroundColor: 'white' }}>
        <ResponsiveContainer>
          <BarChart 
            data={transformedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="country" 
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
            />
            <Tooltip />
            <Legend />
            {products.map((product, index) => (
              <Bar 
                key={product}
                dataKey={product}
                fill={colors[index % colors.length]}
                radius={[4, 4, 0, 0]}
                {...(chartType === 'stacked' ? { stackId: 'a' } : {})}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="chart-response">
      {summary && (
        <div className="response-summary">
          <p className="summary-text">{summary}</p>
        </div>
      )}

      <div className="response-content">
        <div className="tab-navigation">
          <div className="tab-buttons">
            {/* <button 
              className={`tab-button ${activeTab === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveTab('chart')}
            >
              Chart
            </button> */}
            <button 
              className={`tab-button ${activeTab === 'data' ? 'active' : ''}`}
              onClick={() => setActiveTab('data')}
            >
              Data
            </button>
            <button 
              className={`tab-button ${activeTab === 'sql' ? 'active' : ''}`}
              onClick={() => setActiveTab('sql')}
            >
              SQL
            </button>
          </div>
        </div>

        {activeTab === 'chart' && (
          <>
            <div className="chart-type-controls">
              <div className="chart-type-group">
                <span className="chart-type-label">Advices</span>
                <select 
                  value={chartType} 
                  onChange={(e) => setChartType(e.target.value)}
                  className="chart-type-select"
                >
                  <option value="grouped">Grouped Column</option>
                  <option value="stacked">Stacked Column</option>
                </select>
              </div>
              <button 
                className="download-button"
                onClick={handleDownload}
                title="Download chart"
              >
                <svg 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path 
                    d="M12 16L7 11H10V4H14V11H17L12 16Z" 
                    fill="currentColor"
                  />
                  <path 
                    d="M20 18H4V20H20V18Z" 
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
            {/* <div className="chart-container">
              {renderChart()}
            </div> */}
          </>
        )}

        {activeTab === 'sql' && sqlQuery && (
          <div className="sql-container">
            <div className="sql-header">
              <span className="sql-title">SQL Query</span>
              <button 
                className="copy-button"
                onClick={() => {
                  navigator.clipboard.writeText(sqlQuery);
                }}
                title="Copy SQL"
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
            <SyntaxHighlighter 
              language="sql"
              style={docco}
              customStyle={{
                backgroundColor: '#f8f9fa',
                padding: '1rem',
                borderRadius: '0.5rem',
                fontSize: '0.9rem',
                lineHeight: '1.5'
              }}
            >
              {sqlQuery}
            </SyntaxHighlighter>
          </div>
        )}

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
      </div>
    </div>
  );
}

export default ChartResponse; 