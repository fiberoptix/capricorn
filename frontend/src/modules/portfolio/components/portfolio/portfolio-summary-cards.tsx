/**
 * PortfolioSummaryCards Component
 * Reusable 5-card summary display for portfolio financial metrics
 * Can show individual portfolio or aggregated totals across all portfolios
 */

'use client'

import { DollarSign, BarChart3, CheckCircle, AlertTriangle, Wallet } from 'lucide-react'

export interface SummaryData {
  total_value: number
  investment_value: number
  after_tax_value: number
  tax_liability: number
  cash_on_hand: number
}

interface PortfolioSummaryCardsProps {
  summary: SummaryData
  isLoading?: boolean
}

export function PortfolioSummaryCards({ summary, isLoading }: PortfolioSummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map(i => (
          <div key={i} className="bg-gray-100 rounded-lg p-4 h-24 animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Card 1: Total Value (Investment + Cash) */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-center">
          <DollarSign className="h-6 w-6 text-blue-600" />
          <div className="ml-3">
            <p className="text-sm font-medium text-blue-900">Total Value</p>
            <p className="text-lg font-bold text-blue-700">
              ${(summary?.total_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Card 2: Securities Value (Investment Only) */}
      <div className="bg-indigo-50 rounded-lg p-4">
        <div className="flex items-center">
          <BarChart3 className="h-6 w-6 text-indigo-600" />
          <div className="ml-3">
            <p className="text-sm font-medium text-indigo-900">Securities Value</p>
            <p className="text-lg font-bold text-indigo-700">
              ${(summary?.investment_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Card 3: Tax Liability */}
      <div className="bg-red-50 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          <div className="ml-3">
            <p className="text-sm font-medium text-red-900">Tax Liability</p>
            <p className="text-lg font-bold text-red-700">
              ${(summary?.tax_liability || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Card 4: After-Tax Value (After-Tax Securities + Cash) */}
      <div className="bg-green-50 rounded-lg p-4">
        <div className="flex items-center">
          <CheckCircle className="h-6 w-6 text-green-600" />
          <div className="ml-3">
            <p className="text-sm font-medium text-green-900">After-Tax Value</p>
            <p className="text-lg font-bold text-green-700">
              ${(summary?.after_tax_value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>

      {/* Card 5: Cash on Hand */}
      <div className="bg-emerald-50 rounded-lg p-4">
        <div className="flex items-center">
          <Wallet className="h-6 w-6 text-emerald-600" />
          <div className="ml-3">
            <p className="text-sm font-medium text-emerald-900">Cash on Hand</p>
            <p className="text-lg font-bold text-emerald-700">
              ${(summary?.cash_on_hand || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
