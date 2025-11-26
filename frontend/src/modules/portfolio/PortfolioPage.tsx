'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  PieChart, 
  DollarSign, 
  User, 
  Activity,
  AlertCircle,
  CheckCircle,
  Plus,
  Briefcase,
  TrendingDown
} from 'lucide-react'
import { Edit3 } from 'lucide-react'
import { usePortfolios, useCreatePortfolio, useUpdatePortfolio, useDeletePortfolio } from './hooks/use-portfolios'
import { PortfolioForm } from './components/forms/portfolio-form'
import { PortfolioDetail } from './components/portfolio/portfolio-detail'
import { MarketPricesTab } from './components/market-prices/market-prices-tab'
import { InvestorProfileTab } from './components/investor-profile/investor-profile-tab'
import { PortfolioSummaryCards, SummaryData } from './components/portfolio/portfolio-summary-cards'
import { useInvestorProfiles } from './hooks/use-investor-profiles'
import { api } from './lib/api-client'

// Tabs: consolidate to a single Portfolio Overview plus Market/Profile
const tabs = [
  { id: 'overview', name: 'Portfolio Overview', icon: PieChart },
  { id: 'market', name: 'Market Prices', icon: DollarSign },
  { id: 'profile', name: 'Investor Profile', icon: User },
]

// API health status interface
interface HealthStatus {
  status: string
  service: string
  database: string
  timestamp: string
  portfolios_count?: number
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [overviewNonce, setOverviewNonce] = useState(0)
  const [apiHealth, setApiHealth] = useState<HealthStatus | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  
  // Get portfolio data for navigation badges
  const { data: portfolios } = usePortfolios()

  // Check API health on component mount and on demand
  useEffect(() => {
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      // Try to reach FastAPI backend directly
      const response = await fetch('/api/backend/health')
      if (response.ok) {
        const health = await response.json()
        setApiHealth(health)
        setApiError(null)
      } else {
        throw new Error(`API responded with status: ${response.status}`)
      }
    } catch (error) {
      console.error('API Health Check Failed:', error)
      setApiError(error instanceof Error ? error.message : 'Unknown error')
      setApiHealth(null)
    }
  }

  // Get count for each tab badge
  const getTabCount = (tabId: string) => {
    switch (tabId) {
      case 'overview':
        return portfolios?.length || 0
      case 'market':
        return 0 // TODO: Add market prices count
      case 'profile':
        return 0 // TODO: Add investor profiles count
      default:
        return 0
    }
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab apiHealth={apiHealth} overviewNonce={overviewNonce} />
      case 'market':
        return <MarketPricesTab />
      case 'profile':
        return <InvestorProfileTab />
      default:
        return <OverviewTab apiHealth={apiHealth} overviewNonce={overviewNonce} />
    }
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="card">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
                            Welcome to Portfolio Manager
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            Tax-optimization focused portfolio management system
          </p>
          <p className="text-sm text-gray-500">
            Make informed buy/sell decisions by analyzing tax implications vs potential market losses
          </p>
        </div>
      </div>

      {/* Removed DEV banner in favor of compact header status */}

      {/* Tab Navigation */}
      <div className="card">
        <div className="tab-nav">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const count = getTabCount(tab.id)
            return (
              <button
                key={tab.id}
                onClick={() => {
                  if (tab.id === 'overview') {
                    // Even if already active, clicking should reset to overview list
                    setOverviewNonce((n) => n + 1)
                  }
                  setActiveTab(tab.id)
                }}
                className={
                  activeTab === tab.id ? 'tab-button-active' : 'tab-button-inactive'
                }
              >
                <Icon className="h-4 w-4 mr-2" />
                {tab.name}
                {count > 0 && (
                  <span className="ml-2 bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded-full">
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {renderTabContent()}
      </div>
    </div>
  )
}

// Tab Components - Portfolio Overview with consolidated listing
function OverviewTab({ apiHealth, overviewNonce }: { apiHealth: HealthStatus | null, overviewNonce: number }) {
  // overviewNonce forces PortfolioOverviewDashboard to reset internal selection state when the tab is clicked
  return <PortfolioOverviewDashboard key={overviewNonce} apiHealth={apiHealth} />
}

// Consolidated Portfolio Overview Dashboard
function PortfolioOverviewDashboard({ apiHealth }: { apiHealth: HealthStatus | null }) {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [editingPortfolio, setEditingPortfolio] = useState<any | null>(null)
  const [editError, setEditError] = useState<string | null>(null)
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null)
  const [aggregatedData, setAggregatedData] = useState<SummaryData | null>(null)
  const [isLoadingAgg, setIsLoadingAgg] = useState(true)
  const { data: portfolios, isLoading, error } = usePortfolios()
  const { data: profiles } = useInvestorProfiles()
  const createPortfolio = useCreatePortfolio()
  const updatePortfolio = useUpdatePortfolio()
  const deletePortfolio = useDeletePortfolio()
  
  const activeProfileId = profiles?.[0]?.id || 1
  
  // Aggregate data from all portfolios
  useEffect(() => {
    async function aggregateData() {
      if (!portfolios || portfolios.length === 0) {
        setAggregatedData(null)
        setIsLoadingAgg(false)
        return
      }
      
      setIsLoadingAgg(true)
      
      let totalValue = 0
      let totalInvestment = 0
      let totalCash = 0
      let totalTax = 0
      let totalAfterTax = 0
      
      // Fetch data for each portfolio and aggregate
      for (const portfolio of portfolios) {
        try {
          // Market value data
          const mvResp = await api.portfolios.getMarketValue(portfolio.id)
          if (!mvResp.error && mvResp.data) {
            totalValue += mvResp.data.total_market_value || 0
            totalInvestment += mvResp.data.investment_value || 0
            totalCash += mvResp.data.cash_on_hand || 0
          }
          
          // Break-even data for tax calculations
          const beResp = await api.breakEven.analyzePortfolio(portfolio.id, activeProfileId)
          if (!beResp.error && beResp.data?.portfolio_summary) {
            totalTax += beResp.data.portfolio_summary.total_tax_if_all_sold || 0
            totalAfterTax += beResp.data.portfolio_summary.total_after_tax_proceeds || 0
          }
        } catch (err) {
          console.error(`Error aggregating portfolio ${portfolio.id}:`, err)
        }
      }
      
      // After-tax value includes cash
      const afterTaxWithCash = totalAfterTax + totalCash
      
      setAggregatedData({
        total_value: totalValue,
        investment_value: totalInvestment,
        after_tax_value: afterTaxWithCash,
        tax_liability: totalTax,
        cash_on_hand: totalCash,
      })
      
      setIsLoadingAgg(false)
    }
    
    aggregateData()
  }, [portfolios, activeProfileId])

  const handleCreatePortfolio = async (portfolioData: any) => {
    try {
      await createPortfolio.mutateAsync(portfolioData)
      setShowCreateForm(false)
    } catch (error) {
      console.error('Failed to create portfolio:', error)
    }
  }

  if (selectedPortfolioId) {
    return (
      <div className="space-y-4">
        <PortfolioDetail portfolioId={selectedPortfolioId} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border-red-200 bg-red-50">
        <div className="text-center py-12">
          <AlertCircle className="h-16 w-16 mx-auto mb-4 text-red-400" />
          <h3 className="text-lg font-semibold text-red-900 mb-2">Failed to Load Portfolios</h3>
          <p className="text-red-700">{error.message}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Summary - Aggregated Totals */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="text-xl font-semibold">Portfolio Summary</h2>
            <p className="text-gray-600">Combined totals across all {portfolios?.length || 0} portfolios</p>
          </div>
        </div>
        <div className="p-6">
          {aggregatedData ? (
            <PortfolioSummaryCards 
              summary={aggregatedData} 
              isLoading={isLoadingAgg}
            />
          ) : (
            <p className="text-gray-500 text-center py-6">
              {isLoadingAgg ? 'Calculating totals...' : 'No portfolio data available'}
            </p>
          )}
        </div>
      </div>

      {/* Portfolios List */}
      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Your Portfolios</h2>
              <p className="text-gray-600">Manage your investment portfolios</p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>New Portfolio</span>
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading portfolios...</p>
          </div>
        ) : portfolios && portfolios.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {portfolios.map((portfolio) => (
              <PortfolioCard 
                key={portfolio.id} 
                portfolio={portfolio} 
                onSelect={setSelectedPortfolioId}
                onEdit={(p) => {
                  // Ensure we set the exact portfolio the user clicked
                  setEditingPortfolio({ ...p })
                  setShowEditForm(true)
                }}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Briefcase className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Portfolios Yet</h3>
            <p className="text-gray-500 mb-4">
              Create your first portfolio to start tracking investments
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn-primary"
            >
              Create Your First Portfolio
            </button>
          </div>
        )}
      </div>

      {/* Create Portfolio Form */}
      <PortfolioForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onSubmit={handleCreatePortfolio}
        isLoading={createPortfolio.isPending}
      />

      {/* Edit Portfolio Form */}
      <PortfolioForm
        isOpen={showEditForm}
        onClose={() => { setShowEditForm(false); setEditingPortfolio(null); setEditError(null) }}
        initialData={editingPortfolio || undefined}
        onSubmit={async (vals) => {
          if (!editingPortfolio?.id) return
          try {
            await updatePortfolio.mutateAsync({ id: editingPortfolio.id, ...vals })
            setShowEditForm(false)
            setEditingPortfolio(null)
            setEditError(null)
          } catch (e: any) {
            const message = e?.message || 'Failed to update portfolio'
            setEditError(message)
          }
        }}
        onDelete={async () => {
          if (!editingPortfolio?.id) return
          if (window.confirm('Are you sure you want to delete this portfolio? This action cannot be undone.')) {
            try {
              await deletePortfolio.mutateAsync(editingPortfolio.id)
              setShowEditForm(false)
              setEditingPortfolio(null)
              setEditError(null)
            } catch (e: any) {
              const message = e?.message || 'Failed to delete portfolio'
              setEditError(message)
            }
          }
        }}
        isLoading={updatePortfolio.isPending}
        submitError={editError || undefined}
      />
    </div>
  )
}

// MarketPricesTab component is now imported from ../components/market-prices/market-prices-tab

// InvestorProfileTab component is now imported from ../components/investor-profile/investor-profile-tab

// Portfolio Card Component (with unified categories)
function PortfolioCard({ portfolio, onSelect, onEdit }: { portfolio: any; onSelect: (id: number) => void; onEdit: (p: any) => void }) {
  // Category mapping: Trading (green) for real, Tracking (yellow) for tracking, Retirement (blue)
  const isReal = portfolio.type === 'real'
  const category = portfolio.type === 'retirement' ? 'retirement' : isReal ? 'trading' : 'tracking'

  const colorClasses =
    category === 'trading'
      ? { border: 'border-green-200', bg: 'bg-green-50', chip: 'bg-green-100 text-green-800', iconColor: 'text-green-600' }
      : category === 'tracking'
      ? { border: 'border-yellow-200', bg: 'bg-yellow-50', chip: 'bg-yellow-100 text-yellow-800', iconColor: 'text-yellow-600' }
      : { border: 'border-blue-200', bg: 'bg-blue-50', chip: 'bg-blue-100 text-blue-800', iconColor: 'text-blue-600' }

  const label = category === 'trading' ? 'Trading' : category === 'tracking' ? 'Tracking' : 'Retirement'

  return (
    <div
      className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${colorClasses.border} ${colorClasses.bg}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {category === 'trading' ? (
            <TrendingUp className={`h-5 w-5 ${colorClasses.iconColor}`} />
          ) : (
            <Activity className={`h-5 w-5 ${colorClasses.iconColor}`} />
          )}
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${colorClasses.chip}`}>
            {label}
          </span>
        </div>
        <button
          className="inline-flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
          aria-label="Edit Portfolio"
          title="Edit Portfolio"
          onClick={() => onEdit(portfolio)}
        >
          <Edit3 className="h-4 w-4" />
          <span>Edit</span>
        </button>
      </div>

      <h3 className="font-semibold text-gray-900 mb-2">{portfolio.name}</h3>

      <div className="space-y-2 text-sm text-gray-600">
        {portfolio.market && (
          <div className="flex justify-between font-bold">
            <span>Value:</span>
            <span>${Number(portfolio.market.total_market_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
        )}
        {portfolio.market && (
          <div className="flex justify-between">
            <span>Unrealized Gains:</span>
            <span className={Number(portfolio.market.total_gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
              ${Number(portfolio.market.total_gain_loss || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        )}
        <div className="flex justify-between">
          <span>Cash:</span>
          <span>${Number(portfolio.cash_on_hand || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>
        {portfolio.breakEven?.portfolio_summary && (
          <div className="flex justify-between">
            <span>Avg Break-Even:</span>
            <span>{Number(portfolio.breakEven.portfolio_summary.average_break_even_percentage || 0).toFixed(2)}%</span>
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-200">
        <button
          onClick={() => onSelect(portfolio.id)}
          className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View Details →
        </button>
      </div>
    </div>
  )
}