import { useCallback, useEffect, useState } from 'react'

import {
  getApiErrorMessage,
  getDocument,
  getDocumentPages,
  processDocument,
} from '../services/api.js'

export function useDocumentPages(documentId) {
  const [document, setDocument] = useState(null)
  const [pages, setPages] = useState([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [pipelineRequested, setPipelineRequested] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const metadata = await getDocument(documentId)
      setDocument(metadata)
      if (metadata.page_count > 0) {
        setPages(await getDocumentPages(documentId))
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
    if (!pipelineRequested || !['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING'].includes(document?.status)) return undefined
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
    loading,
    starting,
    pipelineRequested,
    error,
    refresh,
    startConversion,
  }
}
