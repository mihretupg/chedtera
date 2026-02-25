const USER_KEY = 'chedtera_user'

export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function authHeaders() {
  const user = getUser()
  if (!user) return {}

  return {
    'x-user-id': String(user.id),
    'x-user-role': user.role,
    'x-user-name': user.name,
    'x-user-phone': user.phone,
  }
}

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
