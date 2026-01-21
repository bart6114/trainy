const API_BASE = '/api/v1'

class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new ApiError(response.status, response.statusText, data)
  }
  return response.json()
}

export async function get<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`)
  return handleResponse<T>(response)
}

export async function post<T, D = unknown>(endpoint: string, data?: D): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  })
  return handleResponse<T>(response)
}

export async function put<T, D = unknown>(endpoint: string, data: D): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function del<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'DELETE',
  })
  return handleResponse<T>(response)
}

export async function patch<T, D = unknown>(endpoint: string, data?: D): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  })
  return handleResponse<T>(response)
}

export { ApiError }
