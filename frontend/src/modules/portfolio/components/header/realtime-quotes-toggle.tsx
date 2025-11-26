/**
 * RealTimeQuotesToggle Component
 * Toggle button for enabling/disabling automatic market price refresh
 */

'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api/backend'

export function RealTimeQuotesToggle() {
  const [enabled, setEnabled] = useState(true)
  const [loading, setLoading] = useState(false)

  // Fetch initial state from backend
  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/market-prices/scheduler/status`)
      if (response.ok) {
        const data = await response.json()
        setEnabled(data.realtime_quotes_enabled ?? true)
      }
    } catch (error) {
      console.error('Failed to fetch scheduler status:', error)
    }
  }

  const handleToggle = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/market-prices/scheduler/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setEnabled(data.realtime_quotes_enabled)
      } else {
        console.error('Failed to toggle real-time quotes')
      }
    } catch (error) {
      console.error('Error toggling real-time quotes:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`
        px-3 py-1.5 rounded-md text-sm font-medium transition-colors
        ${enabled 
          ? 'bg-green-100 text-green-800 hover:bg-green-200' 
          : 'bg-orange-100 text-orange-800 hover:bg-orange-200'
        }
        ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      title={`Real-time quotes are currently ${enabled ? 'ON' : 'OFF'}. Click to toggle.`}
    >
      Real-Time Quotes: {enabled ? 'ON' : 'OFF'}
    </button>
  )
}
