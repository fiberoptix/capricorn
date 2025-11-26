/**
 * PortfolioDetail Component - Standardized UI/UX
 * Comprehensive portfolio management with transaction tracking and break-even analysis
 */

'use client'

import { useState, useMemo, useEffect } from 'react'
import { 
  Plus, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  Edit,
  Trash2,
  RefreshCw,
  BarChart3,
  Wallet
} from 'lucide-react'
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  Chip,
  Divider,
  CircularProgress
} from '@mui/material'
import { 
  ShowChart,
  AccountBalance,
  AttachMoney,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Savings as SavingsIcon,
  Receipt as ReceiptIcon,
  Add as AddIcon
} from '@mui/icons-material'
import { usePortfolio, useUpdatePortfolio, portfolioKeys } from '../../hooks/use-portfolios'
import { useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api-client'
import { usePortfolioTransactions, useCreateTransaction, useUpdateTransaction, useDeleteTransaction } from '../../hooks/use-transactions'
import { usePortfolioBreakEven } from '../../hooks/use-break-even'
import { useInvestorProfiles } from '../../hooks/use-investor-profiles'
import { DataTable, Column } from '../ui/data-table'
import { TransactionForm } from '../forms/transaction-form'
import { Transaction } from '../../lib/api-client'
import { formatRecommendation, getRecommendationColor } from '../../hooks/use-break-even'
import { BreakEvenAnalytics } from '../analytics/break-even-analytics'
import { PortfolioAnalyticsDashboard } from '../analytics/portfolio-analytics-dashboard'
import { CashOnHandCard } from './cash-on-hand-card'

interface PortfolioDetailProps {
  portfolioId: number
  investorProfileId?: number
}

type AugmentedFields = {
  current_price?: number
  total_value?: number
  gain_loss_amount?: number
  gain_loss_percentage?: number
  break_even_percent?: number
  transaction_date_ts?: number
}

// Format currency helper
const formatCurrency = (value: number) => 
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)

// Summary Card Component
interface SummaryCardProps {
  label: string
  value: string
  icon: React.ReactNode
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info'
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, icon, color = 'primary' }) => {
  const colorMap = {
    primary: { bg: 'primary.50', text: 'primary.main' },
    success: { bg: 'success.light', text: 'success.dark' },
    warning: { bg: 'warning.light', text: 'warning.dark' },
    error: { bg: 'error.light', text: 'error.dark' },
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

export function PortfolioDetail({ portfolioId, investorProfileId }: PortfolioDetailProps) {
  const [showTransactionForm, setShowTransactionForm] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const queryClient = useQueryClient()

  // Dynamic investor profile detection
  const { data: profiles, isLoading: profilesLoading } = useInvestorProfiles()
  const activeProfileId = investorProfileId || profiles?.[0]?.id || 1
  
  // Debug logging for profile ID detection
  useEffect(() => {
    if (!profilesLoading) {
      console.log('Portfolio Detail - Profile Detection:', {
        provided: investorProfileId,
        available: profiles?.map(p => ({ id: p.id, name: p.name })),
        using: activeProfileId
      })
    }
  }, [investorProfileId, profiles, activeProfileId, profilesLoading])

  // Data hooks
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio(portfolioId)
  const { data: transactions, isLoading: transactionsLoading } = usePortfolioTransactions(portfolioId)
  // Only fetch break-even data when we have a valid profile ID
  const { data: breakEvenData, isLoading: breakEvenLoading } = usePortfolioBreakEven(portfolioId, activeProfileId)
  const updatePortfolio = useUpdatePortfolio()
  const [marketSummary, setMarketSummary] = useState<{ total_market_value?: number; investment_value?: number; cash_on_hand?: number } | null>(null)
  const [lastUpdatedLabel, setLastUpdatedLabel] = useState<string>('—')
  const [statusText, setStatusText] = useState<string>('Last Updated: —')
  const nyFmt = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'America/New_York' })
  // Refresh market value summary on mount, when transactions/break-even change, and on window focus
  useEffect(() => {
    const fetchMarket = async () => {
      const resp = await api.portfolios.getMarketValue(portfolioId)
      if (!resp.error) setMarketSummary(resp.data as any)
    }
    fetchMarket()
  }, [portfolioId, transactions, breakEvenData])

  useEffect(() => {
    const onFocus = async () => {
      const resp = await api.portfolios.getMarketValue(portfolioId)
      if (!resp.error) setMarketSummary(resp.data as any)
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [portfolioId])

  useEffect(() => {
    const getLastUpdated = async () => {
      try {
        const resp = await api.marketPrices.getAll()
        if (!resp.error && resp.data && resp.data.length > 0) {
          const maxTs = resp.data
            .map((p: any) => new Date(p.last_updated).getTime())
            .filter((n: number) => !isNaN(n))
            .reduce((a: number, b: number) => Math.max(a, b), 0)
          if (maxTs) {
            const d = new Date(maxTs)
            const label = nyFmt.format(d)
            setLastUpdatedLabel(label)
            setStatusText(`Last Updated: ${label}`)
          }
        }
      } catch {
        // ignore
      }
    }
    getLastUpdated()
  }, [transactions])
  
  // Mutations
  const createTransaction = useCreateTransaction()
  const updateTransaction = useUpdateTransaction()
  const deleteTransaction = useDeleteTransaction()

  // Handlers
  const handleCreateTransaction = async (transactionData: any) => {
    try {
      await createTransaction.mutateAsync(transactionData)
      setShowTransactionForm(false)
      setEditingTransaction(null)
      // Refresh portfolio data to update values
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
      queryClient.invalidateQueries({ queryKey: portfolioKeys.detail(portfolioId) })
    } catch (error) {
      console.error('Failed to create transaction:', error)
    }
  }

  const handleEditTransaction = (transaction: Transaction) => {
    setEditingTransaction(transaction)
    setShowTransactionForm(true)
  }

  const handleUpdateTransaction = async (id: number, transactionData: any) => {
    try {
      await updateTransaction.mutateAsync({ id, ...transactionData })
      setShowTransactionForm(false)
      setEditingTransaction(null)
      // Refresh portfolio data to update values
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
      queryClient.invalidateQueries({ queryKey: portfolioKeys.detail(portfolioId) })
    } catch (error) {
      console.error('Failed to update transaction:', error)
    }
  }

  const handleCloseForm = () => {
    setShowTransactionForm(false)
    setEditingTransaction(null)
  }

  const handleDeleteTransaction = async (transactionId: number) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await deleteTransaction.mutateAsync(transactionId)
        // Refresh portfolio data to update values
        queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
        queryClient.invalidateQueries({ queryKey: portfolioKeys.detail(portfolioId) })
      } catch (error) {
        console.error('Failed to delete transaction:', error)
      }
    }
  }

  const handleUpdateCash = async (newAmount: number) => {
    // Use the specific cash update endpoint
    const response = await api.portfolios.updateCash(portfolioId, newAmount)
    if (response.error) {
      throw new Error(response.error)
    }
    
    // Refresh portfolio data including the main list
    queryClient.invalidateQueries({ queryKey: portfolioKeys.all })
    queryClient.invalidateQueries({ queryKey: portfolioKeys.detail(portfolioId) })
    
    // Refresh market summary to include updated cash
    const mv = await api.portfolios.getMarketValue(portfolioId)
    if (!mv.error) setMarketSummary(mv.data as any)
  }

  const handleRefreshQuotes = async () => {
    // Track whether any prices were actually updated during the refresh call
    let updatedCount = 0
    try {
      setStatusText(`Last Checked: ${nyFmt.format(new Date())}`)
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/market-prices/refresh`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: true })
      }).then(async r => { 
        if (r.ok) { 
          const j = await r.json(); 
          updatedCount = Number(j?.updated_count || 0) 
        }
      })
    } catch {}
    try {
      const resp = await api.marketPrices.getAll()
      if (!resp.error && resp.data && resp.data.length > 0) {
        const maxTs = resp.data
          .map((p: any) => new Date(p.last_updated).getTime())
          .filter((n: number) => !isNaN(n))
          .reduce((a: number, b: number) => Math.max(a, b), 0)
        if (maxTs) {
          const d = new Date(maxTs)
          const label = nyFmt.format(d)
          setLastUpdatedLabel(label)
          setStatusText(`${updatedCount > 0 ? 'Last Updated' : 'Last Checked'}: ${label}`)
        }
        // refresh dependent analytics and header numbers
        const mv = await api.portfolios.getMarketValue(portfolioId)
        if (!mv.error) setMarketSummary(mv.data as any)
        // trigger break-even to recalc with new prices
        try {
          const be = await api.breakEven.analyzePortfolio(portfolioId, activeProfileId)
          window.dispatchEvent(new Event('break-even-updated'))
        } catch {}
      }
    } catch {}
  }

  const augmentedTransactions = useMemo(() => {
    return (transactions || []).map((item) => {
      const be = breakEvenData?.transactions?.find((b: any) => b.transaction_id === item.id)
      // Use data from transaction API (already includes current_price, current_value, gain_loss)
      const current_price = item.current_price || be?.current_price
      const total_value = item.current_value || ((item.quantity || 0) * (item.price_per_share || 0))
      const gain_loss_amount = item.gain_loss ?? be?.financial_analysis?.current_gain_loss
      const cost_basis = (item.quantity || 0) * (item.price_per_share || 0)
      const gain_loss_percentage = gain_loss_amount && cost_basis ? (gain_loss_amount / cost_basis) * 100 : (be?.financial_analysis?.gain_loss_percentage || 0)
      const break_even_percent = be?.break_even_analysis?.loss_required_percentage ?? -1
      // Parse date without timezone conversion for sorting
      const transaction_date_ts = typeof item.transaction_date === 'string' && item.transaction_date.match(/^\d{4}-\d{2}-\d{2}/)
        ? new Date(item.transaction_date + 'T12:00:00').getTime()  // Add noon time to avoid timezone issues
        : new Date(item.transaction_date).getTime() || 0
      return {
        ...item,
        current_price,
        total_value,
        gain_loss_amount,
        gain_loss_percentage,
        break_even_percent,
        transaction_date_ts,
      } as Transaction & AugmentedFields
    })
  }, [transactions, breakEvenData])

  // Table columns for transactions
  const transactionColumns: Column<Transaction & AugmentedFields>[] = [
    {
      key: 'transaction_date_ts',
      header: 'Date',
      accessor: (item) => {
        // Display date exactly as stored without timezone conversion
        if (typeof item.transaction_date === 'string' && item.transaction_date.match(/^\d{4}-\d{2}-\d{2}/)) {
          const datePart = item.transaction_date.split('T')[0]
          const [year, month, day] = datePart.split('-')
          return `${month}/${day}/${year}`
        }
        return new Date(item.transaction_date).toLocaleDateString()
      },
      sortable: true,
    },
    {
      key: 'ticker',
      header: 'Stock',
      accessor: (item) => (
        <span className="font-medium text-gray-900">{item.ticker}</span>
      ),
      sortable: true,
    },
    {
      key: 'transaction_type',
      header: 'Type',
      accessor: (item) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          item.transaction_type === 'buy' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {item.transaction_type === 'buy' ? 'Buy' : 'Sell'}
        </span>
      ),
      sortable: true,
    },
    {
      key: 'quantity',
      header: 'Shares',
      accessor: (item) => item.quantity?.toLocaleString() || '0',
      sortable: true,
      className: 'text-right',
    },
    {
      key: 'price_per_share',
      header: 'Price',
      accessor: (item) => `$${item.price_per_share?.toFixed(2) || '0.00'}`,
      sortable: true,
      className: 'text-right',
    },
    {
      key: 'current_price',
      header: 'Value',
      accessor: (item) => {
        // Use current_price from transaction API or fall back to break-even data
        const currentPrice = item.current_price
        return currentPrice !== undefined && currentPrice !== null ? `$${Number(currentPrice).toFixed(2)}` : '—'
      },
      sortable: true,
      className: 'text-right',
    },
    {
      key: 'gain_loss_amount',
      header: 'Total / Gain-Loss',
      accessor: (item) => {
        const total = (item as any).total_value as number
        const gain = (item as any).gain_loss_amount as number | undefined
        const gainPct = (item as any).gain_loss_percentage as number | undefined
        return (
          <div className="flex flex-col items-end leading-tight">
            <span className="text-gray-900">${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            <span className={`text-xs ${gain !== undefined && gain >= 0 ? 'text-green-700' : 'text-red-700'}`}>
              {gain === undefined ? '—' : `${gain >= 0 ? '+' : ''}$${Math.abs(gain).toLocaleString('en-US', { minimumFractionDigits: 2 })} (${gainPct?.toFixed?.(1) ?? '0.0'}%)`}
            </span>
          </div>
        )
      },
      sortable: true,
      className: 'text-right',
    },
    {
      key: 'break_even_percent',
      header: 'Break-Even Analysis',
      accessor: (item) => {
        if (item.transaction_type !== 'buy') {
          return <span className="text-gray-400 text-xs">N/A</span>
        }

        const breakEvenTransaction = breakEvenData?.transactions?.find(
          (be: any) => be.transaction_id === item.id
        )
        
        if (!breakEvenTransaction) {
          return <span className="text-gray-400 text-xs">Calculating...</span>
        }

        return (
          <BreakEvenAnalytics 
            transactionData={breakEvenTransaction}
            className="min-w-[300px]"
          />
        )
      },
      sortable: true,
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (item) => (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => handleEditTransaction(item)}
            className="text-blue-600 hover:text-blue-800 text-sm"
            title="Edit Transaction"
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleDeleteTransaction(item.id)}
            className="text-red-600 hover:text-red-800 text-sm"
            title="Delete Transaction"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
      className: 'text-center',
    },
  ]

  if (portfolioLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!portfolio) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography color="error">Portfolio not found</Typography>
      </Box>
    )
  }

  const isRetirement = portfolio.type === 'retirement' || portfolio.type === '401k' || portfolio.type === 'IRA'
  const totalValue = marketSummary?.total_market_value || breakEvenData?.portfolio_summary?.total_current_value || 0
  const securitiesValue = marketSummary?.investment_value || breakEvenData?.portfolio_summary?.total_current_value || 0
  const taxLiability = breakEvenData?.portfolio_summary?.total_tax_if_all_sold || (marketSummary?.total_gain_loss || 0) * 0.356
  const afterTaxValue = Number(totalValue) - Number(taxLiability)
  const cashOnHand = marketSummary?.cash_on_hand ?? portfolio?.cash_on_hand ?? 0

  return (
    <Box>
      {/* Header - Blue gradient like TAXES */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 2, 
          mb: 2, 
          background: isRetirement 
            ? 'linear-gradient(135deg, #7b1fa2 0%, #4a148c 100%)'
            : 'linear-gradient(135deg, #1976d2 0%, #0d47a1 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            {isRetirement ? (
              <AccountBalance sx={{ fontSize: 36 }} />
            ) : (
              <ShowChart sx={{ fontSize: 36 }} />
            )}
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold', lineHeight: 1.2 }}>
                {portfolio.name}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {isRetirement ? 'Retirement Account' : 'Real Money Portfolio'} • {transactions?.length || 0} transactions
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label={portfolio.type} 
              size="small"
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'white',
                fontWeight: 'bold',
                textTransform: 'capitalize'
              }} 
            />
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              {statusText}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard 
            label="Total Value"
            value={formatCurrency(Number(totalValue))}
            icon={<AttachMoney />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard 
            label="Securities Value"
            value={formatCurrency(Number(securitiesValue))}
            icon={<TrendingUp />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard 
            label="Tax Liability"
            value={formatCurrency(Number(taxLiability))}
            icon={<WarningIcon />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard 
            label="After-Tax Value"
            value={formatCurrency(afterTaxValue)}
            icon={<CheckCircleIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <SummaryCard 
            label="Cash on Hand"
            value={formatCurrency(Number(cashOnHand))}
            icon={<SavingsIcon />}
            color="success"
          />
        </Grid>
      </Grid>

      {/* Enhanced Portfolio Analytics Dashboard */}
      {breakEvenData && (
        <Box sx={{ mb: 2 }}>
          <PortfolioAnalyticsDashboard 
            breakEvenData={breakEvenData}
            transactions={augmentedTransactions}
          />
        </Box>
      )}

      {/* Transactions Section */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ p: 2 }}>
          {/* Section Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ 
              display: 'inline-block',
              bgcolor: 'primary.main',
              color: 'white',
              px: 2,
              py: 0.5,
              borderRadius: 1,
              fontSize: '0.85rem',
              fontWeight: 'bold',
            }}>
              📋 Transactions ({transactions?.length || 0})
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                color="success"
                startIcon={<RefreshCw className="h-4 w-4" />}
                onClick={handleRefreshQuotes}
              >
                Get Live Quotes
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setShowTransactionForm(true)}
              >
                Add Transaction
              </Button>
            </Box>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {transactionsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={32} />
            </Box>
          ) : (
            <DataTable
              data={augmentedTransactions}
              columns={transactionColumns}
              searchable={true}
              searchPlaceholder="Search transactions by ticker, type, or date..."
              emptyMessage="No transactions yet. Add your first transaction to get started!"
              compact
            />
          )}
        </CardContent>
      </Card>

      {/* Cash on Hand Card */}
      <CashOnHandCard
        portfolioId={portfolioId}
        cashOnHand={portfolio?.cash_on_hand || 0}
        onUpdate={handleUpdateCash}
      />

      {/* Footer Note */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Break-Even Analysis:</strong> Shows how much each position can drop before you lose money after paying capital gains tax.
          Tax calculations are based on your Profile settings.
        </Typography>
      </Paper>

      {/* Transaction Form Modal */}
      <TransactionForm
        isOpen={showTransactionForm}
        onClose={handleCloseForm}
        onSubmit={handleCreateTransaction}
        onUpdate={handleUpdateTransaction}
        portfolioId={portfolioId}
        initialData={editingTransaction || undefined}
        mode={editingTransaction ? 'edit' : 'create'}
        isLoading={createTransaction.isPending || updateTransaction.isPending}
      />
    </Box>
  )
}
