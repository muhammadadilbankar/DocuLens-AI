import { useCallback, useEffect, useState } from 'react'

import { deleteDocument, getApiErrorMessage, getDocuments } from '../services/api.js'

export function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      setDocuments(await getDocuments())
      setError('')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const remove = async (documentId) => {
    setDeletingId(documentId)
    setError('')
    try {
      const result = await deleteDocument(documentId)
      setDocuments((current) => current.filter((document) => document.id !== documentId))
      return result
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
      return null
    } finally {
      setDeletingId(null)
    }
  }

  return { documents, loading, deletingId, error, refresh, remove }
}
