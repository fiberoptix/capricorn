/**
 * CashOnHandCard Component
 * Displays and allows editing of uninvested cash in a portfolio
 */

'use client'

import { useState } from 'react'
import { DollarSign, Edit, X, Check } from 'lucide-react'

interface CashOnHandCardProps {
  portfolioId: number
  cashOnHand: number
  onUpdate: (newAmount: number) => Promise<void>
}

export function CashOnHandCard({ portfolioId, cashOnHand, onUpdate }: CashOnHandCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(cashOnHand.toString())
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleEdit = () => {
    setEditValue(cashOnHand.toString())
    setError(null)
    setIsEditing(true)
  }

  const handleCancel = () => {
    setEditValue(cashOnHand.toString())
    setError(null)
    setIsEditing(false)
  }

  const handleSave = async () => {
    const numValue = parseFloat(editValue)
    
    // Validation
    if (isNaN(numValue)) {
      setError('Please enter a valid number')
      return
    }
    
    if (numValue < 0) {
      setError('Cash on hand cannot be negative')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      await onUpdate(numValue)
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update cash on hand')
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-5 w-5 text-green-600" />
            <h3 className="text-lg font-semibold">Cash on Hand</h3>
          </div>
          {!isEditing && (
            <button
              onClick={handleEdit}
              className="btn-secondary flex items-center space-x-1"
              title="Edit cash on hand"
            >
              <Edit className="h-4 w-4" />
              <span>Edit</span>
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {!isEditing ? (
          <div>
            <div className="text-3xl font-bold text-gray-900">
              ${cashOnHand.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Uninvested cash available in this portfolio
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label htmlFor="cash-amount" className="block text-sm font-medium text-gray-700 mb-2">
                Cash Amount ($)
              </label>
              <input
                id="cash-amount"
                type="number"
                step="0.01"
                min="0"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="0.00"
                disabled={isSaving}
                autoFocus
              />
              {error && (
                <p className="mt-2 text-sm text-red-600">{error}</p>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="btn-primary flex items-center space-x-1 flex-1"
              >
                <Check className="h-4 w-4" />
                <span>{isSaving ? 'Saving...' : 'Save'}</span>
              </button>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="btn-secondary flex items-center space-x-1"
              >
                <X className="h-4 w-4" />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
