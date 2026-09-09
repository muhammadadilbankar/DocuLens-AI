import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  headers: { Accept: 'application/json' },
  timeout: 5000,
})

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export default api

