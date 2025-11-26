/**
 * Portfolio Analytics Dashboard
 * Phase 9: Advanced portfolio-level break-even analysis and visualizations
 */

import React, { useMemo, useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Shield, 
  Target, 
  PieChart,
  BarChart3,
  Zap,
  Settings,
  Info
} from 'lucide-react'

interface PortfolioAnalyticsDashboardProps {
  breakEvenData: any
  transactions?: any[]
  className?: string
}

export function PortfolioAnalyticsDashboard({ breakEvenData, transactions, className = '' }: PortfolioAnalyticsDashboardProps) {
  const [activeView, setActiveView] = useState<'overview' | 'risk' | 'scenarios'>('overview')

  // Calculate analytics from break-even data
  const analytics = useMemo(() => {
    if (!breakEvenData) return null

    const txArray: any[] = Array.isArray(breakEvenData.transactions)
      ? breakEvenData.transactions
      : breakEvenData.analysis
      ? Object.values(breakEvenData.analysis).flat()
      : []

    const validTransactions = txArray.filter((t: any) => t.position_status === 'gain')

    // Risk distribution
    const highRisk = validTransactions.filter(t => (t.break_even_analysis?.loss_required_percentage || 0) < 5).length
    const mediumRisk = validTransactions.filter(t => {
      const pct = t.break_even_analysis?.loss_required_percentage || 0
      return pct >= 5 && pct < 15
    }).length
    const lowRisk = validTransactions.filter(t => (t.break_even_analysis?.loss_required_percentage || 0) >= 15).length

    // Tax efficiency metrics
    const totalGains = validTransactions.reduce(
      (sum: number, t: any) => sum + (t?.financial_analysis?.current_gain_loss || 0),
      0
    )
    const totalTaxes = validTransactions.reduce(
      (sum: number, t: any) => sum + (t?.tax_analysis?.total_tax_owed || 0),
      0
    )
    const averageTaxRate = totalGains > 0 ? (totalTaxes / totalGains) * 100 : 0

    // Opportunity analysis (recommendation-based)
    const considerSelling = validTransactions.filter(t => t.recommendation === 'consider_selling')
    const monitor = validTransactions.filter(t => t.recommendation === 'monitor_closely')
    const hold = validTransactions.filter(t => t.recommendation === 'hold')
    const potentialTaxSavings = considerSelling.reduce((sum, t) => {
      const currentTax = t.tax_analysis?.total_tax_owed || 0
      // Estimate tax savings if sold at break-even (zero gains)
      return sum + currentTax
    }, 0)

    // Unrealized gains across ALL transactions (including losses)
    // Use augmented transactions if available, otherwise fall back to break-even data
    const totalUnrealizedGainsAll = (transactions || txArray).reduce(
      (sum: number, t: any) => sum + (t?.gain_loss_amount || t?.gain_loss || t?.financial_analysis?.current_gain_loss || 0),
      0
    )

    return {
      totalPositions: validTransactions.length,
      riskDistribution: { highRisk, mediumRisk, lowRisk },
      averageTaxRate,
      potentialTaxSavings,
      totalTaxLiability: totalTaxes,
      totalUnrealizedGains: totalUnrealizedGainsAll,
      considerSellingCount: considerSelling.length,
      recommendations: {
        hold: hold.length,
        monitor: monitor.length,
        consider: considerSelling.length,
      }
    }
  }, [breakEvenData])

  if (!analytics) {
    return (
      <div className={`bg-gray-50 rounded-lg p-6 ${className}`}>
        <p className="text-gray-500 text-center">No break-even analytics available</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg border ${className}`}>
      {/* Header with View Toggle */}
      <div className="border-b px-4 py-2">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-gray-900 flex items-center">
            <BarChart3 className="h-4 w-4 mr-2 text-blue-600" />
            Advanced Analytics Dashboard
          </h3>
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setActiveView('overview')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                activeView === 'overview' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveView('risk')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                activeView === 'risk' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Risk Analysis
            </button>
            <button
              onClick={() => setActiveView('scenarios')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                activeView === 'scenarios' 
                  ? 'bg-white text-blue-600 shadow-sm' 
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Scenarios
            </button>
          </div>
        </div>
      </div>

      <div className="px-4 py-3">
        {activeView === 'overview' && (
          <OverviewAnalytics analytics={analytics} breakEvenData={breakEvenData} />
        )}
        {activeView === 'risk' && (
          <RiskAnalytics analytics={analytics} breakEvenData={breakEvenData} />
        )}
        {activeView === 'scenarios' && (
          <ScenarioAnalytics analytics={analytics} breakEvenData={breakEvenData} />
        )}
      </div>
    </div>
  )
}

// Overview Analytics Component
function OverviewAnalytics({ analytics, breakEvenData }: { analytics: any, breakEvenData: any }) {
  return (
    <div className="space-y-3">
      {/* Recommendation Summary Strip */}
      <div className="bg-gray-50 rounded-lg px-3 py-2 border">
        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✅ Hold: {analytics.recommendations.hold}
          </span>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            ⚠️ Monitor: {analytics.recommendations.monitor}
          </span>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            🚨 Consider Selling: {analytics.recommendations.consider}
          </span>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <MetricCard
          icon={<Target className="h-5 w-5" />}
          title="Avg Break-Even"
          value={`${breakEvenData.portfolio_summary?.average_break_even_percentage?.toFixed(1) || '0.0'}%`}
          subtitle="Loss required"
          color="blue"
        />
        <MetricCard
          icon={<AlertTriangle className="h-5 w-5" />}
          title="Tax Efficiency"
          value={`${analytics.averageTaxRate.toFixed(1)}%`}
          subtitle="Avg tax rate"
          color="orange"
        />
        <MetricCard
          icon={<TrendingUp className="h-5 w-5" />}
          title="Unrealized Gains"
          value={`$${analytics.totalUnrealizedGains.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle="Current gains"
          color="green"
        />
        <MetricCard
          icon={<Zap className="h-5 w-5" />}
          title="Tax Liability"
          value={`$${analytics.totalTaxLiability.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle="If sold today"
          color="red"
        />
      </div>

      {/* Action Items */}
      {analytics.considerSellingCount > 0 && (
        <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg px-3 py-2">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="font-medium text-red-800 text-sm">⚠️ Immediate Attention Required</h4>
              <p className="text-red-700 text-xs mt-0.5">
                {analytics.considerSellingCount} position{analytics.considerSellingCount !== 1 ? 's' : ''} flagged as "Consider Selling" due to high tax risk. Potential tax savings: ${analytics.potentialTaxSavings.toLocaleString()}.
              </p>
              <p className="text-red-600 text-xs mt-1">
                💡 These positions have low break-even thresholds and may benefit from profit-taking.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Risk Analytics Component
function RiskAnalytics({ analytics }: { analytics: any, breakEvenData: any }) {
  const total = analytics.totalPositions
  const { highRisk, mediumRisk, lowRisk } = analytics.riskDistribution

  return (
    <div className="space-y-3">
      {/* Risk Distribution */}
      <div className="bg-gray-50 rounded-lg px-3 py-2">
        <h4 className="font-medium text-gray-800 mb-2 flex items-center text-sm">
          <Shield className="h-4 w-4 mr-2" />
          Risk Distribution Analysis
        </h4>
        
        <div className="space-y-2">
          <RiskBar
            label="High Risk"
            count={highRisk}
            total={total}
            color="bg-red-500"
            description="<5% drop to break-even"
          />
          <RiskBar
            label="Medium Risk"
            count={mediumRisk}
            total={total}
            color="bg-yellow-500"
            description="5-15% drop to break-even"
          />
          <RiskBar
            label="Low Risk"
            count={lowRisk}
            total={total}
            color="bg-green-500"
            description=">15% drop to break-even"
          />
        </div>
      </div>

      {/* Risk Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-blue-50 rounded-lg px-3 py-2">
          <h5 className="font-medium text-blue-800 text-sm">🎯 Portfolio Risk Score</h5>
          <div className="text-xl font-bold text-blue-700">
            {calculateRiskScore(analytics.riskDistribution, total)}
          </div>
          <p className="text-blue-600 text-xs">Based on position risk distribution</p>
        </div>
        
        <div className="bg-green-50 rounded-lg px-3 py-2">
          <h5 className="font-medium text-green-800 text-sm">💰 Optimization Score</h5>
          <div className="text-xl font-bold text-green-700">
            {calculateOptimizationScore(analytics.averageTaxRate)}%
          </div>
          <p className="text-green-600 text-xs">Tax efficiency rating</p>
        </div>
      </div>
    </div>
  )
}

// Scenario Analytics Component
function ScenarioAnalytics({ analytics, breakEvenData }: { analytics: any, breakEvenData: any }) {
  return (
    <div className="space-y-3">
      <div className="bg-yellow-50 rounded-lg px-3 py-2">
        <h4 className="font-medium text-yellow-800 mb-2 flex items-center text-sm">
          <Settings className="h-4 w-4 mr-2" />
          What-If Scenarios
        </h4>
        
        <div className="space-y-2">
          <ScenarioCard
            title="Market Correction (-10%)"
            impact={`${analytics.riskDistribution.highRisk + analytics.riskDistribution.mediumRisk} positions affected`}
            action="Consider reducing high-risk positions"
            severity="warning"
          />
          
          <ScenarioCard
            title="Tax Rate Increase"
            impact={`Tax liability could increase by $${(analytics.totalTaxLiability * 0.1).toLocaleString()}`}
            action="Accelerate selling of profitable positions"
            severity="info"
          />
          
          <ScenarioCard
            title="Immediate Liquidation"
            impact={`Total after-tax value: $${(breakEvenData.portfolio_summary?.total_after_tax_proceeds || 0).toLocaleString()}`}
            action={`Current tax bill: $${analytics.totalTaxLiability.toLocaleString()}`}
            severity="neutral"
          />
        </div>
      </div>
    </div>
  )
}

// Helper Components
function MetricCard({ icon, title, value, subtitle, color }: {
  icon: React.ReactNode
  title: string
  value: string
  subtitle: string
  color: 'blue' | 'green' | 'red' | 'orange'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    orange: 'bg-orange-50 text-orange-600'
  }

  return (
    <div className="bg-white border rounded-lg px-3 py-2">
      <div className={`inline-flex p-1.5 rounded-lg ${colorClasses[color]}`}>
        {icon}
      </div>
      <div className="mt-1.5">
        <p className="text-xs font-medium text-gray-600">{title}</p>
        <p className="text-xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-500">{subtitle}</p>
      </div>
    </div>
  )
}

function RiskBar({ label, count, total, color, description }: any) {
  const percentage = total > 0 ? (count / total) * 100 : 0
  
  return (
    <div>
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium text-gray-700">{label}</span>
        <span className="text-xs text-gray-500">{count} of {total}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-0.5">
        <div 
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <p className="text-xs text-gray-400 mt-0.5">{description}</p>
    </div>
  )
}

function ScenarioCard({ title, impact, action, severity }: {
  title: string
  impact: string
  action: string
  severity: 'warning' | 'info' | 'neutral'
}) {
  const severityClasses = {
    warning: 'border-yellow-200 bg-yellow-50',
    info: 'border-blue-200 bg-blue-50',
    neutral: 'border-gray-200 bg-gray-50'
  }

  return (
    <div className={`border rounded-lg px-2 py-1.5 ${severityClasses[severity]}`}>
      <h6 className="font-medium text-gray-800 text-sm">{title}</h6>
      <p className="text-xs text-gray-600">{impact}</p>
      <p className="text-xs text-gray-500 mt-0.5">💡 {action}</p>
    </div>
  )
}

// Helper Functions
function calculateRiskScore(riskDistribution: any, total: number): string {
  if (total === 0) return 'N/A'
  
  const { highRisk, mediumRisk, lowRisk } = riskDistribution
  const score = ((lowRisk * 100) + (mediumRisk * 60) + (highRisk * 20)) / total
  
  if (score >= 80) return 'A+'
  if (score >= 70) return 'A'
  if (score >= 60) return 'B+'
  if (score >= 50) return 'B'
  if (score >= 40) return 'C+'
  return 'C'
}

function calculateOptimizationScore(averageTaxRate: number): string {
  // Lower tax rates get higher scores
  if (averageTaxRate <= 15) return '95'
  if (averageTaxRate <= 20) return '85'
  if (averageTaxRate <= 25) return '75'
  if (averageTaxRate <= 30) return '65'
  return '50'
}