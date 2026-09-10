import { useCallback, useEffect, useState } from 'react'

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

  const refresh = useCallback(async () => {
    try {
      const metadata = await getDocument(documentId)
      setDocument(metadata)
      if (metadata.page_count > 0) {
        const [pageData, entityData] = await Promise.all([
          getDocumentPages(documentId),
          getDocumentEntities(documentId),
        ])
        setPages(pageData)
        setEntities(entityData)
      }
      setError('')
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    refresh()
  }, [refresh])

  useEffect(() => {
    if (!pipelineRequested || !['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING', 'EXTRACTING_ENTITIES'].includes(document?.status)) return undefined
    const timer = window.setInterval(refresh, 1500)
    return () => window.clearInterval(timer)
  }, [document?.status, pipelineRequested, refresh])

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
