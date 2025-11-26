/**
 * PortfolioForm Component - Standardized UI/UX
 * Form for creating and editing portfolios
 */

'use client'

import { useState, useEffect } from 'react'
import { Modal, ModalFooter } from '../ui/modal'
import { Portfolio } from '../../lib/api-client'
import { Briefcase, TrendingUp, Eye, PiggyBank } from 'lucide-react'

interface PortfolioFormProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (portfolio: Omit<Portfolio, 'id' | 'created_at' | 'updated_at'>) => void
  initialData?: Partial<Portfolio>
  isLoading?: boolean
  submitError?: string
  onDelete?: () => void
}

export function PortfolioForm({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isLoading = false,
  submitError,
  onDelete,
}: PortfolioFormProps) {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    type: (initialData?.type as 'real' | 'tracking' | 'retirement') || 'real',
    description: initialData?.description || '',
    cash_on_hand: initialData?.cash_on_hand || 0,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Keep form state in sync when editing a different portfolio or when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: initialData?.name || '',
        type: (initialData?.type as 'real' | 'tracking' | 'retirement') || 'real',
        description: initialData?.description || '',
        cash_on_hand: initialData?.cash_on_hand || 0,
      })
      setErrors({})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialData?.id])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Portfolio name is required'
    } else if (formData.name.length < 2) {
      newErrors.name = 'Portfolio name must be at least 2 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) return

    onSubmit({
      name: formData.name.trim(),
      type: formData.type,
      description: formData.description.trim(),
      cash_on_hand: formData.cash_on_hand,
    })
  }

  const handleClose = () => {
    setFormData({
      name: initialData?.name || '',
      type: (initialData?.type as 'real' | 'tracking' | 'retirement') || 'real',
      description: initialData?.description || '',
      cash_on_hand: initialData?.cash_on_hand || 0,
    })
    setErrors({})
    onClose()
  }

  const portfolioTypes = [
    {
      value: 'real',
      label: 'Trading',
      description: 'Track actual investments with real money',
      icon: <TrendingUp className="h-5 w-5" />,
      color: 'blue',
    },
    {
      value: 'tracking',
      label: 'Tracking',
      description: 'Monitor hypothetical investments for research',
      icon: <Eye className="h-5 w-5" />,
      color: 'purple',
    },
    {
      value: 'retirement',
      label: 'Retirement',
      description: '401k/IRA retirement accounts',
      icon: <PiggyBank className="h-5 w-5" />,
      color: 'green',
    },
  ]

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={initialData?.id ? 'Edit Portfolio' : 'Create New Portfolio'}
      subtitle={initialData?.id ? 'Update your portfolio settings' : 'Set up a new investment portfolio'}
      icon={<Briefcase className="h-5 w-5 text-white" />}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {submitError && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
            {submitError}
          </div>
        )}

        {/* Portfolio Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-semibold text-gray-700 mb-2">
            Portfolio Name
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => {
              const sanitized = e.target.value.replace(/[\x00-\x1F]/g, '')
              setFormData(prev => ({ ...prev, name: sanitized }))
            }}
            placeholder="e.g., My Investment Portfolio"
            className={`
              block w-full px-4 py-3 border-2 rounded-lg
              font-sans text-base
              transition-colors duration-200
              focus:ring-0 focus:border-blue-500 focus:outline-none
              ${errors.name ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'}
            `}
            disabled={isLoading}
          />
          {errors.name && (
            <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
              <span>⚠️</span> {errors.name}
            </p>
          )}
        </div>

        {/* Portfolio Type - Card Selection */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-3">
            Portfolio Type
          </label>
          <div className="grid grid-cols-1 gap-3">
            {portfolioTypes.map((type) => (
              <label
                key={type.value}
                className={`
                  relative flex items-center p-4 rounded-lg border-2 cursor-pointer
                  transition-all duration-200
                  ${formData.type === type.value 
                    ? `border-${type.color}-500 bg-${type.color}-50 ring-2 ring-${type.color}-200` 
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }
                  ${formData.type === type.value && type.color === 'blue' ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' : ''}
                  ${formData.type === type.value && type.color === 'purple' ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200' : ''}
                  ${formData.type === type.value && type.color === 'green' ? 'border-green-500 bg-green-50 ring-2 ring-green-200' : ''}
                `}
              >
                <input
                  type="radio"
                  name="type"
                  value={type.value}
                  checked={formData.type === type.value}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    type: e.target.value as 'real' | 'tracking' | 'retirement'
                  }))}
                  className="sr-only"
                  disabled={isLoading}
                />
                <div className={`
                  p-2 rounded-lg mr-4
                  ${formData.type === type.value && type.color === 'blue' ? 'bg-blue-500 text-white' : ''}
                  ${formData.type === type.value && type.color === 'purple' ? 'bg-purple-500 text-white' : ''}
                  ${formData.type === type.value && type.color === 'green' ? 'bg-green-500 text-white' : ''}
                  ${formData.type !== type.value ? 'bg-gray-100 text-gray-500' : ''}
                `}>
                  {type.icon}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{type.label}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                </div>
                {formData.type === type.value && (
                  <div className={`
                    absolute right-4 top-1/2 -translate-y-1/2
                    w-5 h-5 rounded-full flex items-center justify-center
                    ${type.color === 'blue' ? 'bg-blue-500' : ''}
                    ${type.color === 'purple' ? 'bg-purple-500' : ''}
                    ${type.color === 'green' ? 'bg-green-500' : ''}
                  `}>
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Form Footer */}
        <ModalFooter>
          {initialData?.id && onDelete && (
            <button
              type="button"
              onClick={onDelete}
              disabled={isLoading}
              className="mr-auto px-4 py-2.5 text-sm font-semibold text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              🗑️ Delete
            </button>
          )}
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
            className="px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {isLoading ? '⏳ Saving...' : (initialData?.id ? '✓ Update Portfolio' : '+ Create Portfolio')}
          </button>
        </ModalFooter>
      </form>
    </Modal>
  )
}
