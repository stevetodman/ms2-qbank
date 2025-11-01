/**
 * Authentication context for managing user session state
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import * as authApi from '../api/auth.ts';

const TOKEN_STORAGE_KEY = 'auth_token';

interface AuthContextValue {
  user: authApi.UserProfile | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: authApi.RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: authApi.ProfileUpdateData) => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<authApi.UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(() => {
    // Initialize from localStorage on mount
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load user profile when token changes
  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const profile = await authApi.getCurrentUser(token);
        setUser(profile);
      } catch (err) {
        console.error('Failed to load user profile:', err);
        setError(err instanceof Error ? err.message : 'Failed to load user');
        // Clear invalid token
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    void loadUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await authApi.login({ email, password });

      // Store token
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setToken(response.access_token);

      // User profile will be loaded by useEffect
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: authApi.RegisterData) => {
    try {
      setLoading(true);
      setError(null);

      // Register user (returns profile, not token)
      await authApi.register(data);

      // Auto-login after registration
      await login(data.email, data.password);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await authApi.logout(token);
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      // Clear state regardless of API call success
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setToken(null);
      setUser(null);
      setError(null);
    }
  };

  const updateUserProfile = async (data: authApi.ProfileUpdateData) => {
    if (!token) {
      throw new Error('Not authenticated');
    }

    try {
      setLoading(true);
      setError(null);
      const updatedProfile = await authApi.updateProfile(token, data);
      setUser(updatedProfile);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Update failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextValue = {
    user,
    token,
    loading,
    error,
    login,
    register,
    logout,
    updateUserProfile,
    isAuthenticated: !!user && !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access authentication context
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
