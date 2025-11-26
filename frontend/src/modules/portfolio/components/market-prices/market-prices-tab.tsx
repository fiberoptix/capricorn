/**
 * Market Prices Tab - Standardized UI/UX
 * Manage stock prices across all portfolios
 */

'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { 
  DollarSign, 
  RefreshCw, 
  Edit, 
  Save, 
  X, 
  AlertTriangle,
  TrendingUp,
  Clock,
  Upload
} from 'lucide-react'
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Alert
} from '@mui/material'
import { 
  AttachMoney,
  Update as UpdateIcon,
  ShowChart,
  Schedule
} from '@mui/icons-material'
import { 
  useMarketPrices, 
  useUpdateMarketPrice,
  useBulkUpdateMarketPrices
} from '../../hooks/use-market-prices'
import api from '../../lib/api-client'
import { useQueryClient } from '@tanstack/react-query'
import { DataTable } from '../ui/data-table'
import { CurrencyInput } from '../ui/currency-input'
import { API_V1_URL } from '../../../../config/api'

interface RefreshStatus {
  is_running: boolean
  total_symbols: number
  completed_symbols: number
  minutes_remaining: number
  progress_percent: number
  status_message: string
  error: string | null
}

interface EditingPrice {
  ticker: string
  price: number
}

// Summary Card Component
interface SummaryCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  color?: 'primary' | 'success' | 'warning' | 'info'
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, icon, color = 'primary' }) => {
  const colorMap = {
    primary: { bg: 'primary.50', text: 'primary.main' },
    success: { bg: 'success.light', text: 'success.dark' },
    warning: { bg: 'warning.light', text: 'warning.dark' },
    info: { bg: 'info.light', text: 'info.dark' },
  }
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ 
            p: 1, 
            borderRadius: 1, 
            bgcolor: colorMap[color].bg,
            color: colorMap[color].text,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colorMap[color].text }}>
              {value}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export function MarketPricesTab() {
  const queryClient = useQueryClient()
  const [editingPrice, setEditingPrice] = useState<EditingPrice | null>(null)
  const [bulkUpdateMode, setBulkUpdateMode] = useState(false)
  const [bulkPrices, setBulkPrices] = useState<Record<string, number>>({})
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null)
  const statusPollRef = useRef<NodeJS.Timeout | null>(null)

  // Data hooks
  const { data: marketPrices, isLoading: loadingPrices, error: pricesError, refetch } = useMarketPrices()

  const lastUpdatedLabel = (() => {
    if (!marketPrices || marketPrices.length === 0) return '—'
    const maxTs = marketPrices
      .map(p => new Date(p.last_updated).getTime())
      .filter(n => !isNaN(n))
      .reduce((a, b) => Math.max(a, b), 0)
    if (!maxTs) return '—'
    const d = new Date(maxTs)
    const fmt = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'America/New_York' })
    return fmt.format(d)
  })()

  const [statusText, setStatusText] = useState<string>('Last Updated: —')
  
  useEffect(() => {
    if (lastUpdatedLabel && lastUpdatedLabel !== '—') {
      setStatusText(`Last Updated: ${lastUpdatedLabel}`)
    }
  }, [lastUpdatedLabel])

  // Function to check refresh status
  const checkRefreshStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh-status`)
      if (response.ok) {
        const data = await response.json()
        setRefreshStatus(data.status)
        return data.status
      }
    } catch (error) {
      console.error('Failed to check refresh status:', error)
    }
    return null
  }, [])

  // Poll for status updates during background refresh
  const startStatusPolling = useCallback(() => {
    // Clear any existing poll
    if (statusPollRef.current) {
      clearInterval(statusPollRef.current)
    }
    
    // Poll every 2 seconds
    statusPollRef.current = setInterval(async () => {
      const status = await checkRefreshStatus()
      
      if (status) {
        // Update status text with progress
        if (status.is_running) {
          setStatusText(status.status_message)
        }
        
        if (!status.is_running) {
          // Refresh complete - stop polling
          if (statusPollRef.current) {
            clearInterval(statusPollRef.current)
            statusPollRef.current = null
          }
          
          // Refresh data
          await refetch()
          queryClient.invalidateQueries({ queryKey: ['break-even'] })
          queryClient.invalidateQueries({ queryKey: ['portfolios'] })
          queryClient.invalidateQueries({ queryKey: ['portfolio-summary'] })
          
          // Update status text
          const nyFmt = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'America/New_York' })
          const nowLabel = nyFmt.format(new Date())
          if (status.completed_symbols > 0) {
            setStatusText(`Last Updated: ${nowLabel} (${status.completed_symbols} prices)`)
          } else {
            setStatusText(`Last Checked: ${nowLabel}`)
          }
          
          // Clear status after a delay
          setTimeout(() => setRefreshStatus(null), 5000)
        }
      }
    }, 2000)
  }, [checkRefreshStatus, refetch, queryClient])

  // Check for active refresh on mount
  useEffect(() => {
    checkRefreshStatus()
  }, [checkRefreshStatus])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (statusPollRef.current) {
        clearInterval(statusPollRef.current)
      }
    }
  }, [])
  
  // Mutation hooks
  const updatePriceMutation = useUpdateMarketPrice()
  const bulkUpdateMutation = useBulkUpdateMarketPrices()

  // Handle individual price update
  const handleUpdatePrice = async (ticker: string, newPrice: number) => {
    try {
      await updatePriceMutation.mutateAsync({ ticker, price: newPrice })
      setEditingPrice(null)
    } catch (error) {
      console.error('Failed to update price:', error)
    }
  }

  // Handle bulk price update
  const handleBulkUpdate = async () => {
    if (Object.keys(bulkPrices).length === 0) return
    
    const updates = Object.entries(bulkPrices).map(([ticker, price]) => ({
      ticker,
      current_price: price
    }))
    
    try {
      await bulkUpdateMutation.mutateAsync(updates)
      setBulkPrices({})
      setBulkUpdateMode(false)
    } catch (error) {
      console.error('Failed to bulk update prices:', error)
    }
  }

  const startEditing = (ticker: string, currentPrice: number) => {
    setEditingPrice({ ticker, price: currentPrice })
  }

  const cancelEditing = () => {
    setEditingPrice(null)
  }

  const updateBulkPrice = (ticker: string, price: number) => {
    setBulkPrices(prev => ({ ...prev, [ticker]: price }))
  }

  const formatLastUpdated = (timestamp: string) => {
    const date = new Date(timestamp)
    // Format as "H:MM AM/PM on M/D" in EST timezone
    const timeFmt = new Intl.DateTimeFormat('en-US', { 
      hour: 'numeric', 
      minute: '2-digit', 
      hour12: true,
      timeZone: 'America/New_York' 
    })
    const dateFmt = new Intl.DateTimeFormat('en-US', { 
      month: 'numeric', 
      day: 'numeric',
      timeZone: 'America/New_York' 
    })
    return `${timeFmt.format(date)} on ${dateFmt.format(date)}`
  }

  const handleGetLiveQuotes = async () => {
    setStatusText('Starting refresh...')
    try {
      // Start background refresh
      const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: true }),
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('🚀 Background refresh started:', data.status?.status_message)
        setRefreshStatus(data.status)
        setStatusText(data.status?.status_message || 'Fetching prices...')
        
        // Start polling for status updates
        startStatusPolling()
      }
    } catch (err) {
      console.error('Refresh failed:', err)
      setStatusText('Error starting refresh')
    }
  }

  const handleClearAndRebuild = async () => {
    try {
      setStatusText('Clearing tickers...')
      const resetRes = await api.marketPrices.resetToPortfolioHoldings()
      
      if (!resetRes.error) {
        setStatusText('Starting refresh...')
        
        // Start background refresh
        const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ force: true }),
        })
        
        if (response.ok) {
          const data = await response.json()
          console.log('🚀 Background refresh started:', data.status?.status_message)
          setRefreshStatus(data.status)
          setStatusText(data.status?.status_message || 'Fetching prices...')
          
          // Start polling for status updates
          startStatusPolling()
        }
      } else {
        setStatusText('Error clearing prices')
      }
    } catch (error) {
      console.error('Failed to clear and rebuild with live quotes:', error)
      setStatusText('Error updating prices')
    }
  }

  // Table columns
  const columns = [
    {
      key: 'ticker',
      header: 'Ticker',
      accessor: (price: any) => (
        <span className="font-semibold text-blue-600">{price.ticker}</span>
      ),
    },
    {
      key: 'current_price',
      header: 'Current Price',
      accessor: (price: any) => (
        <div className="flex items-center space-x-2">
          {editingPrice?.ticker === price.ticker ? (
            <div className="flex items-center space-x-2">
              <CurrencyInput
                value={editingPrice?.price || 0}
                onChange={(value) => setEditingPrice(prev => prev ? { ...prev, price: value } : null)}
                className="w-28"
              />
              <button
                onClick={() => editingPrice && handleUpdatePrice(editingPrice.ticker, editingPrice.price)}
                disabled={updatePriceMutation.isPending || !editingPrice}
                className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                title="Save"
              >
                <Save className="h-4 w-4" />
              </button>
              <button
                onClick={cancelEditing}
                className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
                title="Cancel"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : bulkUpdateMode ? (
            <CurrencyInput
              value={bulkPrices[price.ticker] || price.current_price}
              onChange={(value) => updateBulkPrice(price.ticker, value)}
              className="w-28"
            />
          ) : (
            <div className="flex items-center space-x-2">
              <span className="font-semibold">${price.current_price?.toFixed(2) || '0.00'}</span>
              <button
                onClick={() => startEditing(price.ticker, price.current_price || 0)}
                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                title="Edit price"
              >
                <Edit className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'last_updated',
      header: 'Last Updated',
      accessor: (price: any) => (
        <div className="flex items-center space-x-2 text-gray-600">
          <Clock className="h-4 w-4" />
          <span className="text-sm">{formatLastUpdated(price.last_updated)}</span>
        </div>
      ),
    },
  ]

  // Calculate stats
  const totalPrices = marketPrices?.length || 0
  const updatedPrices = marketPrices?.filter(p => new Date().getTime() - new Date(p.last_updated).getTime() < 86400000).length || 0
  const avgPrice = marketPrices?.length 
    ? (marketPrices.reduce((sum, p) => sum + (p.current_price || 0), 0) / marketPrices.length)
    : 0

  if (pricesError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load market prices: {pricesError.message}
      </Alert>
    )
  }

  return (
    <Box>
      {/* Header Section */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ p: 2 }}>
          {/* Section Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2, flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Box sx={{ 
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'success.main',
                color: 'white',
                px: 2,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.85rem',
                fontWeight: 'bold',
                mb: 1,
              }}>
                <AttachMoney sx={{ fontSize: 18 }} />
                Market Prices
              </Box>
              <Typography variant="body2" color="text.secondary">
                Manage stock prices across all portfolios
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {refreshStatus?.is_running && (
                  <CircularProgress size={14} sx={{ color: 'info.main' }} />
                )}
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: refreshStatus?.is_running ? 'info.main' : 'primary.main', 
                    fontWeight: 'bold' 
                  }}
                >
                  {statusText}
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {bulkUpdateMode ? (
                <>
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    startIcon={bulkUpdateMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <Save className="h-4 w-4" />}
                    onClick={handleBulkUpdate}
                    disabled={bulkUpdateMutation.isPending || Object.keys(bulkPrices).length === 0}
                  >
                    Save All ({Object.keys(bulkPrices).length})
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<X className="h-4 w-4" />}
                    onClick={() => {
                      setBulkUpdateMode(false)
                      setBulkPrices({})
                    }}
                  >
                    Cancel
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    startIcon={refreshStatus?.is_running ? <CircularProgress size={16} color="inherit" /> : <RefreshCw className="h-4 w-4" />}
                    onClick={handleGetLiveQuotes}
                    disabled={refreshStatus?.is_running}
                  >
                    {refreshStatus?.is_running ? 'Refreshing...' : 'Get Live Quotes'}
                  </Button>
                  <Button
                    variant="contained"
                    color="warning"
                    size="small"
                    startIcon={<AlertTriangle className="h-4 w-4" />}
                    onClick={handleClearAndRebuild}
                    disabled={refreshStatus?.is_running}
                  >
                    Clear & Rebuild
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Upload className="h-4 w-4" />}
                    onClick={() => setBulkUpdateMode(true)}
                    disabled={!marketPrices || marketPrices.length === 0 || refreshStatus?.is_running}
                  >
                    Bulk Update
                  </Button>
                </>
              )}
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Summary Cards */}
          {!loadingPrices && (
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={4}>
                <SummaryCard 
                  label="Total Prices"
                  value={totalPrices}
                  icon={<ShowChart />}
                  color="primary"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <SummaryCard 
                  label="Updated Today"
                  value={updatedPrices}
                  icon={<UpdateIcon />}
                  color="success"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <SummaryCard 
                  label="Avg Price"
                  value={`$${avgPrice.toFixed(0)}`}
                  icon={<Schedule />}
                  color="info"
                />
              </Grid>
            </Grid>
          )}

          {/* Data Table */}
          {loadingPrices ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : marketPrices && marketPrices.length > 0 ? (
            <DataTable
              data={marketPrices}
              columns={columns}
            />
          ) : (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <DollarSign className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <Typography variant="h6" gutterBottom>
                No Market Prices Yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Market prices will be automatically created when you add transactions.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Bulk Update Help */}
      {bulkUpdateMode && (
        <Paper sx={{ p: 2, bgcolor: 'info.light', border: '1px solid', borderColor: 'info.main' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: 'info.dark', mb: 0.5 }}>
            📝 Bulk Update Mode
          </Typography>
          <Typography variant="body2" color="info.dark">
            Edit any prices in the table above, then click "Save All" to update multiple prices at once.
            Only modified prices will be updated.
          </Typography>
        </Paper>
      )}

      {/* Footer Note */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Note:</strong> Market prices are used to calculate portfolio values and break-even analysis.
          Click "Get Live Quotes" to fetch current prices from the market.
        </Typography>
      </Paper>
    </Box>
  )
}
