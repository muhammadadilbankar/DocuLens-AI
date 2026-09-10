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

export async function getDocuments() {
  const { data } = await api.get('/documents')
  return data
}

export async function processDocument(documentId) {
  const { data } = await api.post(`/documents/${documentId}/process`)
  return data
}

export async function deleteDocument(documentId) {
  const { data } = await api.delete(`/documents/${documentId}`, { timeout: 30000 })
  return data
}

export async function getDocumentPages(documentId) {
  const { data } = await api.get(`/documents/${documentId}/pages`)
  return data
}

export async function getDocumentPage(documentId, pageNumber) {
  const { data } = await api.get(`/documents/${documentId}/pages/${pageNumber}`)
  return data
}

export async function getDocumentEntities(documentId, pageNumber) {
  const { data } = await api.get(`/documents/${documentId}/entities`, {
    params: pageNumber ? { page_number: pageNumber } : undefined,
  })
  return data
}

export async function searchDocument(documentId, query, limit = 5) {
  const { data } = await api.post(
    `/documents/${documentId}/search`,
    { query, limit },
    { timeout: 30000 },
  )
  return data
}

export async function getDocumentExport(documentId, format) {
  const response = await api.get(`/documents/${documentId}/export`, {
    params: { format },
    responseType: 'blob',
    timeout: 120000,
  })
  const disposition = response.headers['content-disposition'] ?? ''
  const filenameMatch = disposition.match(/filename="?([^";]+)"?/i)
  return {
    blob: response.data,
    filename: filenameMatch?.[1] ?? `document-export.${format}`,
  }
}

export function getPageImageUrl(imagePath) {
  return new URL(imagePath, `${api.defaults.baseURL}/`).toString()
}

export function getApiErrorMessage(error) {
  return error.response?.data?.detail ?? 'Unable to reach the document service. Please try again.'
}

export default api
