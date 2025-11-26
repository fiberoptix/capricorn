/**
 * TransactionForm Component - Standardized UI/UX
 * Form for creating and editing stock transactions
 */

'use client'

import { useState, useEffect } from 'react'
import { Modal, ModalFooter } from '../ui/modal'
import { CurrencyInput } from '../ui/currency-input'
import { Transaction } from '../../lib/api-client'
import { Receipt, TrendingUp, TrendingDown, Calendar, Hash, DollarSign } from 'lucide-react'

interface TransactionFormProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (transaction: Omit<Transaction, 'id' | 'created_at' | 'updated_at'>) => void
  onUpdate?: (id: number, transaction: Partial<Transaction>) => void
  portfolioId: number
  initialData?: Partial<Transaction>
  isLoading?: boolean
  mode?: 'create' | 'edit'
}

export function TransactionForm({
  isOpen,
  onClose,
  onSubmit,
  onUpdate,
  portfolioId,
  initialData,
  isLoading = false,
  mode = 'create',
}: TransactionFormProps) {
  const [formData, setFormData] = useState({
    ticker: initialData?.ticker || '',
    transaction_type: initialData?.transaction_type || 'buy' as const,
    quantity: initialData?.quantity || 0,
    price_per_share: initialData?.price_per_share || 0,
    transaction_date: initialData?.transaction_date 
      ? (typeof initialData.transaction_date === 'string' && initialData.transaction_date.match(/^\d{4}-\d{2}-\d{2}/)
          ? initialData.transaction_date.split('T')[0]
          : new Date(initialData.transaction_date).toISOString().split('T')[0])
      : new Date().toISOString().split('T')[0],
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Sync form data when modal opens or initialData changes
  useEffect(() => {
    if (isOpen && initialData) {
      setFormData({
        ticker: initialData.ticker || '',
        transaction_type: initialData.transaction_type || 'buy',
        quantity: initialData.quantity || 0,
        price_per_share: initialData.price_per_share || 0,
        transaction_date: initialData.transaction_date
          ? new Date(initialData.transaction_date).toISOString().split('T')[0]
          : new Date().toISOString().split('T')[0],
      })
      setErrors({})
    } else if (isOpen && !initialData) {
      setFormData({
        ticker: '',
        transaction_type: 'buy',
        quantity: 0,
        price_per_share: 0,
        transaction_date: new Date().toISOString().split('T')[0],
      })
      setErrors({})
    }
  }, [isOpen, initialData])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.ticker.trim()) {
      newErrors.ticker = 'Stock ticker is required'
    } else if (!/^[A-Z]{1,5}$/.test(formData.ticker.toUpperCase())) {
      newErrors.ticker = 'Ticker must be 1-5 uppercase letters'
    }

    if (formData.quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0'
    }

    if (formData.price_per_share <= 0) {
      newErrors.price_per_share = 'Price must be greater than 0'
    }

    if (!formData.transaction_date) {
      newErrors.transaction_date = 'Date is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    const transactionData = {
      portfolio_id: portfolioId,
      ticker: formData.ticker.toUpperCase().trim(),
      transaction_type: formData.transaction_type,
      quantity: formData.quantity,
      price_per_share: formData.price_per_share,
      transaction_date: formData.transaction_date,
    }

    if (mode === 'edit' && initialData?.id && onUpdate) {
      onUpdate(initialData.id, transactionData)
    } else {
      onSubmit(transactionData)
    }
  }

  const handleClose = () => {
    setFormData({
      ticker: initialData?.ticker || '',
      transaction_type: initialData?.transaction_type || 'buy',
      quantity: initialData?.quantity || 0,
      price_per_share: initialData?.price_per_share || 0,
      transaction_date: initialData?.transaction_date 
        ? new Date(initialData.transaction_date).toISOString().split('T')[0]
        : new Date().toISOString().split('T')[0],
    })
    setErrors({})
    onClose()
  }

  const totalValue = formData.quantity * formData.price_per_share
  const isBuy = formData.transaction_type === 'buy'

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={mode === 'edit' ? 'Edit Transaction' : 'Add New Transaction'}
      subtitle={mode === 'edit' ? 'Update transaction details' : 'Record a stock purchase or sale'}
      icon={<Receipt className="h-5 w-5 text-white" />}
      size="lg"
      variant={isBuy ? 'success' : 'danger'}
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Transaction Type Toggle */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Transaction Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label
              className={`
                relative flex items-center justify-center p-4 rounded-lg border-2 cursor-pointer
                transition-all duration-200
                ${isBuy 
                  ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <input
                type="radio"
                name="transaction_type"
                value="buy"
                checked={isBuy}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  transaction_type: e.target.value as 'buy' | 'sell' 
                }))}
                className="sr-only"
                disabled={isLoading}
              />
              <div className={`p-2 rounded-lg mr-3 ${isBuy ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-500'}`}>
                <TrendingUp className="h-5 w-5" />
              </div>
              <div>
                <div className={`font-semibold ${isBuy ? 'text-green-700' : 'text-gray-700'}`}>Buy</div>
                <div className="text-xs text-gray-500">Purchase shares</div>
              </div>
              {isBuy && (
                <div className="absolute right-3 top-3 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </label>
            
            <label
              className={`
                relative flex items-center justify-center p-4 rounded-lg border-2 cursor-pointer
                transition-all duration-200
                ${!isBuy 
                  ? 'border-red-500 bg-red-50 ring-2 ring-red-200' 
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <input
                type="radio"
                name="transaction_type"
                value="sell"
                checked={!isBuy}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  transaction_type: e.target.value as 'buy' | 'sell' 
                }))}
                className="sr-only"
                disabled={isLoading}
              />
              <div className={`p-2 rounded-lg mr-3 ${!isBuy ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-500'}`}>
                <TrendingDown className="h-5 w-5" />
              </div>
              <div>
                <div className={`font-semibold ${!isBuy ? 'text-red-700' : 'text-gray-700'}`}>Sell</div>
                <div className="text-xs text-gray-500">Sell shares</div>
              </div>
              {!isBuy && (
                <div className="absolute right-3 top-3 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </label>
          </div>
        </div>

        {/* Row 1: Ticker and Date */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="ticker" className="block text-sm font-semibold text-gray-700 mb-2">
              <span className="flex items-center gap-2">
                <Hash className="h-4 w-4 text-gray-400" />
                Stock Ticker
              </span>
            </label>
            <input
              type="text"
              id="ticker"
              value={formData.ticker}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                ticker: e.target.value.toUpperCase() 
              }))}
              placeholder="AAPL"
              className={`
                block w-full px-4 py-3 border-2 rounded-lg uppercase
                font-sans text-base
                transition-colors duration-200
                focus:ring-0 focus:border-blue-500 focus:outline-none
                ${errors.ticker ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'}
              `}
              disabled={isLoading}
              maxLength={5}
            />
            {errors.ticker && (
              <p className="mt-2 text-sm text-red-600">⚠️ {errors.ticker}</p>
            )}
          </div>

          <div>
            <label htmlFor="transaction_date" className="block text-sm font-semibold text-gray-700 mb-2">
              <span className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                Transaction Date
              </span>
            </label>
            <input
              type="date"
              id="transaction_date"
              value={formData.transaction_date}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                transaction_date: e.target.value 
              }))}
              className={`
                block w-full px-4 py-3 border-2 rounded-lg
                font-sans text-base
                transition-colors duration-200
                focus:ring-0 focus:border-blue-500 focus:outline-none
                ${errors.transaction_date ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'}
              `}
              disabled={isLoading}
              max={new Date().toISOString().split('T')[0]}
            />
            {errors.transaction_date && (
              <p className="mt-2 text-sm text-red-600">⚠️ {errors.transaction_date}</p>
            )}
          </div>
        </div>

        {/* Row 2: Quantity and Price */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="quantity" className="block text-sm font-semibold text-gray-700 mb-2">
              <span className="flex items-center gap-2">
                📊 Quantity (Shares)
              </span>
            </label>
            <input
              type="number"
              id="quantity"
              value={formData.quantity || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                quantity: parseFloat(e.target.value) || 0 
              }))}
              placeholder="100"
              min="0"
              step="1"
              className={`
                block w-full px-4 py-3 border-2 rounded-lg text-right
                font-sans text-base
                transition-colors duration-200
                focus:ring-0 focus:border-blue-500 focus:outline-none
                ${errors.quantity ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'}
              `}
              disabled={isLoading}
            />
            {errors.quantity && (
              <p className="mt-2 text-sm text-red-600">⚠️ {errors.quantity}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <span className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-gray-400" />
                Price Per Share
              </span>
            </label>
            <CurrencyInput
              value={formData.price_per_share}
              onChange={(value) => setFormData(prev => ({ 
                ...prev, 
                price_per_share: value 
              }))}
              placeholder="$150.00"
              error={errors.price_per_share}
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Total Value Display */}
        {totalValue > 0 && (
          <div className={`
            rounded-xl p-4 border-2
            ${isBuy ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}
          `}>
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold text-gray-700">Total Transaction Value</span>
              <span className={`text-2xl font-bold ${isBuy ? 'text-green-700' : 'text-red-700'}`}>
                ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {formData.quantity.toLocaleString()} shares × ${formData.price_per_share.toFixed(2)} per share
            </p>
          </div>
        )}

        {/* Form Footer */}
        <ModalFooter>
          <button
            type="button"
            onClick={handleClose}
            disabled={isLoading}
            className="px-4 py-2.5 text-sm font-semibold text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className={`
              px-5 py-2.5 text-sm font-semibold text-white rounded-lg transition-colors disabled:opacity-50
              ${isBuy 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-red-600 hover:bg-red-700'
              }
            `}
          >
            {isLoading 
              ? '⏳ Saving...' 
              : mode === 'edit' 
                ? '✓ Update Transaction' 
                : `${isBuy ? '📈 Buy' : '📉 Sell'} ${formData.ticker || 'Stock'}`
            }
          </button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
