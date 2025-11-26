/**
 * Enhanced Break-Even Analytics Component
 * Phase 9: Advanced visualizations and decision support for tax optimization
 */

import React, { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Calculator, DollarSign, Calendar } from 'lucide-react'
import api from '../../lib/api-client'

interface BreakEvenAnalyticsProps {
  transactionData: any
  investorProfileId?: number
  className?: string
}

export function BreakEvenAnalytics({ transactionData, investorProfileId = 1, className = '' }: BreakEvenAnalyticsProps) {
  const [estimatedSavings, setEstimatedSavings] = useState<number | null>(null)
  const [savingNote, setSavingNote] = useState<string>('')
  
  // Prefer server-provided estimate if available; fallback to client calc only if missing
  useEffect(() => {
    if (!transactionData) return
    const estimate = transactionData.tax_loss_harvest_estimate
    if (estimate && typeof estimate.estimated_savings === 'number') {
      setEstimatedSavings(estimate.estimated_savings)
      setSavingNote(estimate.notes || '')
      return
    }
    // Fallback: do client-side estimate (kept as backup)
    const runFallback = async () => {
      try {
        const isLoss = transactionData.position_status === 'loss'
        if (!isLoss) { setEstimatedSavings(null); return }
        const lossDollars = Math.abs(transactionData.financial_analysis?.current_gain_loss ?? 0)
        if (!lossDollars) { setEstimatedSavings(0); return }
        const profileResp = await api.investorProfiles.getById(investorProfileId)
        if (profileResp.error) throw new Error(profileResp.error)
        const profile = profileResp.data as any
        const localRate = Number(profile?.local_tax_rate || 0)
        const stateCode = String(profile?.state_of_residence || 'NY')
        const prog = await api.investorProfiles.calculateProgressiveTax(investorProfileId, 1, false, false)
        const marginalOrdinary = (prog.data as any)?.marginal_rate || 0
        const state = await api.stateTax.getRatesForState(stateCode)
        const stateRate = (state.data as any)?.capital_gains_rate || 0
        const ordinaryOffset = Math.min(lossDollars, 3000)
        const savings = ordinaryOffset * (marginalOrdinary + stateRate + localRate)
        setEstimatedSavings(savings)
        setSavingNote('Estimate assumes $3,000 ordinary-income offset; excludes wash-sale and carryovers')
      } catch { setEstimatedSavings(null) }
    }
    runFallback()
  }, [transactionData, investorProfileId])

  const breakEven = transactionData.break_even_analysis
  const taxAnalysis = transactionData.tax_analysis
  const financial = transactionData.financial_analysis
  const holding = transactionData.holding_period
  const recommendation = transactionData.recommendation

  // Risk level calculation
  const riskLevel = getRiskLevel(breakEven?.loss_required_percentage || 0)
  const riskColor = getRiskColor(riskLevel)

  // Loss path UI (Tax-loss harvesting)
  if (transactionData?.position_status === 'loss') {
    const lossAmount = Math.abs(transactionData.financial_analysis?.current_gain_loss ?? transactionData.current_gain_loss ?? 0)
    return (
      <div className={`bg-white border rounded-lg ${className}`}>
        <div className="p-3">
          <div className="flex items-center justify-between">
            <div className={`px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800`}>
              Consider Tax-Loss Harvesting
            </div>
            <div className="text-xs">
              {estimatedSavings != null ? (
                <>
                  <span className="text-gray-700">Value </span>
                  <span className="text-green-700 font-semibold">
                    ${estimatedSavings.toLocaleString(undefined,{maximumFractionDigits:0})}
                  </span>
                </>
              ) : (
                <span className="text-gray-500">Estimating...</span>
              )}
            </div>
          </div>
          <div className="mt-1 text-[10px] text-gray-500">Unrealized loss ${lossAmount.toLocaleString()}</div>
          {/* Details removed for compact UI */}
        </div>
      </div>
    )
  }

  return (
      <div className={`bg-white border rounded-lg ${className}`}>
      {/* Main Analytics Row */}
      <div className="p-3">
        <div className="flex items-center justify-between">
          {/* Recommendation Badge */}
          <div className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getRecommendationColor(recommendation)}`}>
            {formatRecommendation(recommendation)}
          </div>
          
          {/* Risk Indicator */}
          <div className="flex items-center space-x-1">
            <span className="text-xs font-medium">{(breakEven?.loss_required_percentage || 0).toFixed(1)}%</span>
          </div>
        </div>

        {/* Risk Progress Bar */}
        <div className="mt-2">
          <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1">
            <span>Risk: {riskLevel}</span>
            <span>{(breakEven?.loss_required_percentage || 0).toFixed(1)}% to break-even</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className={`h-1.5 rounded-full transition-all duration-300 ${riskColor.bg}`}
              style={{ width: `${Math.min(100, (breakEven?.loss_required_percentage || 0) * 5)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Details removed for compact UI */}
    </div>
  )
}

// Helper functions
function getRiskLevel(lossPercentage: number): string {
  if (lossPercentage < 5) return 'High Risk'
  if (lossPercentage < 15) return 'Medium Risk'
  return 'Low Risk'
}

function getRiskColor(riskLevel: string) {
  switch (riskLevel) {
    case 'High Risk':
      return { bg: 'bg-red-500', text: 'text-red-600' }
    case 'Medium Risk':
      return { bg: 'bg-yellow-500', text: 'text-yellow-600' }
    default:
      return { bg: 'bg-green-500', text: 'text-green-600' }
  }
}

function getRecommendationColor(recommendation: string): string {
  switch (recommendation) {
    case 'hold':
      return 'bg-green-100 text-green-800'
    case 'monitor_closely':
      return 'bg-yellow-100 text-yellow-800'
    case 'consider_selling':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function formatRecommendation(recommendation: string): string {
  switch (recommendation) {
    case 'hold':
      return 'Hold'
    case 'monitor_closely':
      return 'Monitor'
    case 'consider_selling':
      return 'Consider Selling'
    default:
      return 'Unknown'
  }
}

function getRecommendationExplanation(recommendation: string, lossPercentage: number): string {
  switch (recommendation) {
    case 'hold':
      return `This position has low tax risk. The stock would need to drop ${lossPercentage.toFixed(1)}% before selling becomes tax-advantageous. Continue holding unless fundamental analysis suggests otherwise.`
    case 'monitor_closely':
      return `Moderate tax risk detected. Watch for market volatility - a ${lossPercentage.toFixed(1)}% decline would make selling tax-neutral. Consider setting price alerts.`
    case 'consider_selling':
      return `High tax risk! The stock only needs to drop ${lossPercentage.toFixed(1)}% to reach break-even after taxes. Consider taking profits now unless you're very confident in near-term performance.`
    default:
      return 'Analysis not available for this position.'
  }
}