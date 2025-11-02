/**
 * API client utility for making HTTP requests
 * Simple fetch wrapper that automatically parses JSON and throws on errors
 */

/**
 * Make an API request
 * @param url - Full URL to request
 * @param options - Fetch options
 * @returns Parsed JSON response
 * @throws Error if response is not ok
 */
export async function apiClient<T = any>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}
