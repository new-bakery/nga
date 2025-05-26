import React, { useEffect, useState } from 'react';
import './Modal.scss';

function Modal({ isOpen, onClose, onConfirm, title, message }) {
  const [isVisible, setIsVisible] = useState(false);
  const [animationClass, setAnimationClass] = useState('');

  useEffect(() => {
    let timer;
    if (isOpen) {
      // First make the modal visible in DOM without animation class
      setIsVisible(true);
      // Then add animation class in the next frame to ensure smooth animation
      timer = setTimeout(() => {
        setAnimationClass('modal-enter');
      }, 10);
    } else if (isVisible) {
      // Start exit animation
      setAnimationClass('modal-exit');
      // Actual removal from DOM happens in the onAnimationEnd handler
    }

    return () => clearTimeout(timer);
  }, [isOpen, isVisible]);

  const handleAnimationEnd = () => {
    if (animationClass === 'modal-exit') {
      setAnimationClass('');
      setIsVisible(false);
    } else if (animationClass === 'modal-enter') {
      setAnimationClass('modal-visible');
    }
  };

  if (!isVisible) return null;

  return (
    <div className="modal-container">
      <div
        className={`modal-overlay ${animationClass}`}
        onClick={onClose}
        onAnimationEnd={handleAnimationEnd}
      >
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h2 className="modal-title">{title}</h2>
            <button className="modal-close" onClick={onClose} aria-label="Close">
              <span aria-hidden="true">×</span>
            </button>
          </div>
          <div className="modal-body">
            <p className="modal-message">{message}</p>
          </div>
          <div className="modal-footer">
            <div className="modal-buttons">
              <button className="modal-button cancel" onClick={onClose}>
                Cancel
              </button>
              <button className="modal-button confirm" onClick={onConfirm}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Modal; 