/**
 * API utility functions with automatic authentication token injection
 */

/**
 * Fetch wrapper that automatically adds authentication token to requests
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = localStorage.getItem('auth_token')
  
  // Merge headers with Authorization header if token exists
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  // Make the request with the token
  const response = await fetch(url, {
    ...options,
    headers,
  })
  
  // If we get a 401, the token might be expired - redirect to login
  if (response.status === 401 && window.location.pathname !== '/login') {
    localStorage.removeItem('auth_token')
    window.location.href = '/login'
  }
  
  return response
}

/**
 * Simple GET request with auth
 */
export async function apiGet(url: string): Promise<Response> {
  return fetchWithAuth(url, { method: 'GET' })
}

/**
 * Simple POST request with auth
 */
export async function apiPost(url: string, data?: any): Promise<Response> {
  return fetchWithAuth(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  })
}
