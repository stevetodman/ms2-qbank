/**
 * Signup/registration page route
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { SignupForm } from '../components/SignupForm.tsx';
import { useAuth } from '../context/AuthContext.tsx';
import '../styles/auth.css';

export function SignupRoute() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <header className="auth-header">
          <h1>MS2 QBank</h1>
          <p>Create your account to start preparing for USMLE Step 1</p>
        </header>
        <SignupForm />
      </div>
    </div>
  );
}
