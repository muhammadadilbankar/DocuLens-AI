import { useCallback, useEffect, useState } from 'react'

import { getHealth } from '../services/api.js'

export function useHealth() {
  const [state, setState] = useState('loading')
  const [health, setHealth] = useState(null)

  const checkHealth = useCallback(async () => {
    setState('loading')

    try {
      const response = await getHealth()
      setHealth(response)
      setState('connected')
    } catch {
      setHealth(null)
      setState('disconnected')
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  return { state, health, checkHealth }
}

