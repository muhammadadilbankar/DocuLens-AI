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

export async function uploadDocument(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post('/documents/upload', formData, {
    timeout: 120000,
    onUploadProgress: ({ loaded, total }) => {
      if (total) onProgress?.(Math.round((loaded * 100) / total))
    },
  })
  return data
}

export async function getDocument(documentId) {
  const { data } = await api.get(`/documents/${documentId}`)
  return data
}

export async function processDocument(documentId) {
  const { data } = await api.post(`/documents/${documentId}/process`)
  return data
}

export async function getDocumentPages(documentId) {
  const { data } = await api.get(`/documents/${documentId}/pages`)
  return data
}

export function getPageImageUrl(imagePath) {
  return new URL(imagePath, `${api.defaults.baseURL}/`).toString()
}

export function getApiErrorMessage(error) {
  return error.response?.data?.detail ?? 'Unable to reach the document service. Please try again.'
}

export default api
