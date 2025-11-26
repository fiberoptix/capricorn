'use client'

import { useEffect, useState } from 'react'

export function HeaderStatus() {
  const [backendOk, setBackendOk] = useState(false)
  const [apiOk, setApiOk] = useState(false)
  const [webOk] = useState(true) // if header renders, web is up
  const [frontendOk] = useState(true) // this component renders from frontend
  const [dbStatus, setDbStatus] = useState<string>('unknown')

  const refresh = async () => {
    try {
      const res = await fetch('/api/backend/health')
      setBackendOk(res.ok)
      if (res.ok) {
        const h = await res.json()
        setDbStatus(h?.database || 'unknown')
      }
      // Simple API check: try list portfolios (public)
      const apiRes = await fetch('/api/backend/api/portfolios')
      setApiOk(apiRes.ok)
    } catch {
      setBackendOk(false)
      setApiOk(false)
      setDbStatus('unknown')
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const countGreen = [backendOk, apiOk, webOk, frontendOk, dbStatus === 'connected'].filter(Boolean).length
  const isAll = countGreen >= 5
  const statusWord = isAll ? 'Online' : 'Error'
  return (
    <div className="flex items-center space-x-2 text-sm text-gray-500">
      <button onClick={refresh} title="Refresh status" className="text-gray-400 hover:text-gray-600">
        ↻
      </button>
      <div>
        Status: <span className={isAll ? 'text-green-600' : 'text-amber-500'}>●</span> {countGreen}/5 {statusWord}
      </div>
    </div>
  )
}

export default HeaderStatus


