/**
 * Login form component
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.tsx';

export function LoginForm() {
  const navigate = useNavigate();
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!email || !password) {
      setFormError('Please enter both email and password');
      return;
    }

    try {
      await login(email, password);
      // Redirect to dashboard on successful login
      navigate('/dashboard');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Sign In</h2>

      {(formError || error) && (
        <div className="error-message" role="alert">
          {formError || error}
        </div>
      )}

      <div className="form-group">
        <label htmlFor="email">
          Email Address
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            disabled={loading}
          />
        </label>
      </div>

      <div className="form-group">
        <label htmlFor="password">
          Password
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            disabled={loading}
            minLength={8}
          />
        </label>
      </div>

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </button>

      <p className="auth-link">
        Don't have an account?{' '}
        <a href="/signup" onClick={(e) => {
          e.preventDefault();
          navigate('/signup');
        }}>
          Sign up
        </a>
      </p>
    </form>
  );
}
