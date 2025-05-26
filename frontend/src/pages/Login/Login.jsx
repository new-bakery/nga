import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../../services/auth';
import './Login.scss';

const Login = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [focusedField, setFocusedField] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [particles, setParticles] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    // Create initial particles
    const initialParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: Math.random() * 4 + 1,
      speedX: (Math.random() - 0.5) * 2,
      speedY: (Math.random() - 0.5) * 2,
    }));
    setParticles(initialParticles);

    const animateParticles = () => {
      setParticles(prevParticles =>
        prevParticles.map(particle => ({
          ...particle,
          x: (particle.x + particle.speedX + window.innerWidth) % window.innerWidth,
          y: (particle.y + particle.speedY + window.innerHeight) % window.innerHeight,
        }))
      );
    };

    const intervalId = setInterval(animateParticles, 50);
    return () => clearInterval(intervalId);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFocus = (field) => {
    setFocusedField(field);
  };

  const handleBlur = () => {
    setFocusedField(null);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await authService.login(credentials.username, credentials.password);
      if (response.access_token) {
        // Add success animation before navigation
        const loginBox = document.querySelector('.login-box');
        loginBox.classList.add('success');
        setTimeout(() => {
          navigate('/home', { replace: true });
        }, 1000);
      }
    } catch (err) {
      setError(err.message || 'Failed to login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="particles-container">
        {particles.map(particle => (
          <div
            key={particle.id}
            className="particle"
            style={{
              left: `${particle.x}px`,
              top: `${particle.y}px`,
              width: `${particle.size}px`,
              height: `${particle.size}px`
            }}
          />
        ))}
      </div>
      <div className="login-background"></div>
      <div className="login-box">
        <div className="logo-container">
        </div>
        <h2>Welcome to {import.meta.env.VITE_APP_NAME}</h2>
        <form onSubmit={handleSubmit} className={isLoading ? 'loading' : ''}>
          {error && (
            <div className="error-message">
              <i className="fas fa-exclamation-circle"></i>
              {error}
            </div>
          )}
          <div className={`form-group ${focusedField === 'username' ? 'focused' : ''} ${credentials.username ? 'has-value' : ''}`}>
            <label htmlFor="username">
              <i className="fas fa-user"></i>
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              onFocus={() => handleFocus('username')}
              onBlur={handleBlur}
              disabled={isLoading}
              required
            />
            <div className="input-border"></div>
            <div className="field-icon">
              <i className="fas fa-user-circle"></i>
            </div>
          </div>
          <div className={`form-group ${focusedField === 'password' ? 'focused' : ''} ${credentials.password ? 'has-value' : ''}`}>
            <label htmlFor="password">
              <i className="fas fa-lock"></i>
              Password
            </label>
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              onFocus={() => handleFocus('password')}
              onBlur={handleBlur}
              disabled={isLoading}
              required
            />
            <div className="input-border"></div>
            <div className="field-icon password-toggle" onClick={togglePasswordVisibility}>
              <i className={`fas ${showPassword ? 'fa-eye-slash' : 'fa-eye'}`}></i>
            </div>
          </div>
          <button type="submit" disabled={isLoading} className="glow-button">
            {isLoading ? (
              <div className="spinner">
                <div className="bounce1"></div>
                <div className="bounce2"></div>
                <div className="bounce3"></div>
              </div>
            ) : (
              <>
                <span>Login</span>
                <i className="fas fa-arrow-right"></i>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login; 