/**
 * Signup/registration form component
 */

import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function SignupForm() {
  const navigate = useNavigate();
  const { register, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [examDate, setExamDate] = useState('');
  const [formError, setFormError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');

    // Validation
    if (!email || !password || !fullName) {
      setFormError('Please fill in all required fields');
      return;
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters');
      return;
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match');
      return;
    }

    try {
      await register({
        email,
        password,
        full_name: fullName,
        exam_date: examDate || undefined,
      });

      // Registration auto-logs in, redirect to dashboard
      navigate('/dashboard');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Registration failed');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>Create Account</h2>

      {(formError || error) && (
        <div className="error-message" role="alert">
          {formError || error}
        </div>
      )}

      <div className="form-group">
        <label htmlFor="fullName">
          Full Name *
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            autoComplete="name"
            disabled={loading}
          />
        </label>
      </div>

      <div className="form-group">
        <label htmlFor="email">
          Email Address *
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
          Password * (minimum 8 characters)
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            disabled={loading}
            minLength={8}
          />
        </label>
      </div>

      <div className="form-group">
        <label htmlFor="confirmPassword">
          Confirm Password *
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            disabled={loading}
            minLength={8}
          />
        </label>
      </div>

      <div className="form-group">
        <label htmlFor="examDate">
          USMLE Step 1 Exam Date (optional)
          <input
            id="examDate"
            type="date"
            value={examDate}
            onChange={(e) => setExamDate(e.target.value)}
            disabled={loading}
          />
        </label>
      </div>

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? 'Creating account...' : 'Create Account'}
      </button>

      <p className="auth-link">
        Already have an account?{' '}
        <a href="/login" onClick={(e) => {
          e.preventDefault();
          navigate('/login');
        }}>
          Sign in
        </a>
      </p>
    </form>
  );
}
