/**
 * API client for user authentication endpoints
 */

import { getBaseUrl } from '../utils/env.ts';

const AUTH_API_BASE = `${getBaseUrl()}/auth`;

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  exam_date: string | null;
  subscription_tier: string;
  subscription_start: string | null;
  subscription_end: string | null;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  exam_date?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ProfileUpdateData {
  full_name?: string;
  exam_date?: string | null;
  notification_preferences?: Record<string, unknown>;
  display_settings?: Record<string, unknown>;
}

/**
 * Register a new user account
 */
export async function register(data: RegisterData): Promise<UserProfile> {
  const response = await fetch(`${AUTH_API_BASE}/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

/**
 * Login with email and password, returns JWT token
 */
export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await fetch(`${AUTH_API_BASE}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

/**
 * Get current authenticated user's profile
 */
export async function getCurrentUser(token: string): Promise<UserProfile> {
  const response = await fetch(`${AUTH_API_BASE}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch user profile');
  }

  return response.json();
}

/**
 * Update current user's profile
 */
export async function updateProfile(
  token: string,
  data: ProfileUpdateData,
): Promise<UserProfile> {
  const response = await fetch(`${AUTH_API_BASE}/me`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update profile');
  }

  return response.json();
}

/**
 * Logout (server acknowledges, client should discard token)
 */
export async function logout(token: string): Promise<void> {
  await fetch(`${AUTH_API_BASE}/logout`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}
