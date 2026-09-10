import { useCallback, useEffect, useRef, useState } from 'react'

import {
  getApiErrorMessage,
  getDocument,
  getDocumentEntities,
  getDocumentPages,
  processDocument,
} from '../services/api.js'

export function useDocumentPages(documentId) {
  const [document, setDocument] = useState(null)
  const [pages, setPages] = useState([])
  const [entities, setEntities] = useState([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [pipelineRequested, setPipelineRequested] = useState(false)
  const [error, setError] = useState('')
  const activeRefreshRef = useRef(null)

  const refresh = useCallback(async () => {
    if (activeRefreshRef.current?.documentId === documentId) return
    const refreshToken = { documentId }
    activeRefreshRef.current = refreshToken
    try {
      const [metadata, pageData, entityData] = await Promise.all([
        getDocument(documentId),
        getDocumentPages(documentId),
        getDocumentEntities(documentId),
      ])
      if (activeRefreshRef.current === refreshToken) {
        setDocument(metadata)
        setPages(pageData)
        setEntities(entityData)
        setError('')
      }
    } catch (requestError) {
      if (activeRefreshRef.current === refreshToken) {
        setError(getApiErrorMessage(requestError))
      }
    } finally {
      if (activeRefreshRef.current === refreshToken) {
        activeRefreshRef.current = null
        setLoading(false)
      }
    }
  }, [documentId])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING', 'EXTRACTING_ENTITIES', 'INDEXING'].includes(document?.status)) return undefined
    const timer = window.setInterval(refresh, 1500)
    return () => window.clearInterval(timer)
  }, [document?.status, refresh])

  const startConversion = async () => {
    setStarting(true)
    setError('')
    try {
      setDocument(await processDocument(documentId))
      setPipelineRequested(true)
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      setStarting(false)
    }
  }

  return {
    document,
    pages,
    entities,
    loading,
    starting,
    pipelineRequested,
    error,
    refresh,
    startConversion,
  }
}
