import React, { useEffect, useRef, useState } from 'react';
import './PlotResponse.scss';

function PlotResponse({ plotHTML }) {
  const plotContainerRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!plotHTML || !plotContainerRef.current) return;

    // Reset loading state when plotHTML changes
    setIsLoading(true);

    // Function to load Plotly if it's not already loaded
    const loadPlotly = () => {
      return new Promise((resolve) => {
        if (window.Plotly) {
          resolve();
          return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.plot.ly/plotly-3.0.1.min.js';
        script.async = true;
        script.onload = () => resolve();
        document.head.appendChild(script);
      });
    };

    // Function to execute the plot HTML and scripts
    const renderPlot = () => {
      // First, set the HTML content
      plotContainerRef.current.innerHTML = plotHTML;

      // Then, find all script tags and execute them
      const scripts = plotContainerRef.current.querySelectorAll('script');
      scripts.forEach(oldScript => {
        const newScript = document.createElement('script');
        
        // Copy all attributes from the original script
        Array.from(oldScript.attributes).forEach(attr => {
          newScript.setAttribute(attr.name, attr.value);
        });
        
        // Copy the content of the script
        newScript.textContent = oldScript.textContent;
        
        // Replace the old script with the new one to trigger execution
        oldScript.parentNode.replaceChild(newScript, oldScript);
      });

      // Set loading to false after a small delay to ensure plot is rendered
      setTimeout(() => {
        setIsLoading(false);
      }, 300);
    };

    // Load Plotly first, then render the plot
    loadPlotly().then(renderPlot);

    // Cleanup function
    return () => {
      // Clean up any resources if needed
    };
  }, [plotHTML]);

  return (
    <div className="plot-response">
      {isLoading && (
        <div className="plot-loading">
          <div className="plot-loading-spinner"></div>
          <p>Loading visualization...</p>
        </div>
      )}
      <div 
        ref={plotContainerRef}
        className={`plot-container ${isLoading ? 'plot-loading-hidden' : ''}`}
      />
    </div>
  );
}

export default PlotResponse; 