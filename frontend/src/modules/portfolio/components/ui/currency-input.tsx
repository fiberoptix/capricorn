/**
 * CurrencyInput Component - Standardized UI/UX
 * Specialized input for currency values with proper formatting
 */

'use client'

import { useState, useEffect } from 'react'

interface CurrencyInputProps {
  value: number
  onChange: (value: number) => void
  placeholder?: string
  className?: string
  disabled?: boolean
  min?: number
  max?: number
  label?: string
  error?: string
}

export function CurrencyInput({
  value,
  onChange,
  placeholder = '$0.00',
  className = '',
  disabled = false,
  min = 0,
  max,
  label,
  error,
}: CurrencyInputProps) {
  const [displayValue, setDisplayValue] = useState('')
  const [isFocused, setIsFocused] = useState(false)

  // Format number as currency for display
  const formatCurrency = (num: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(num)
  }

  // Parse currency string to number
  const parseCurrency = (str: string): number => {
    const cleaned = str.replace(/[^0-9.-]/g, '')
    const parsed = parseFloat(cleaned)
    return isNaN(parsed) ? 0 : parsed
  }

  // Update display value when value prop changes
  useEffect(() => {
    if (!isFocused) {
      setDisplayValue(value > 0 ? formatCurrency(value) : '')
    }
  }, [value, isFocused])

  const handleFocus = () => {
    setIsFocused(true)
    // Show raw number when focused for easier editing
    setDisplayValue(value > 0 ? value.toString() : '')
  }

  const handleBlur = () => {
    setIsFocused(false)
    const numericValue = parseCurrency(displayValue)
    
    // Apply min/max constraints
    let constrainedValue = numericValue
    if (min !== undefined && constrainedValue < min) constrainedValue = min
    if (max !== undefined && constrainedValue > max) constrainedValue = max
    
    onChange(constrainedValue)
    setDisplayValue(constrainedValue > 0 ? formatCurrency(constrainedValue) : '')
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value
    setDisplayValue(inputValue)
    
    if (isFocused) {
      const numericValue = parseCurrency(inputValue)
      onChange(numericValue)
    }
  }

  return (
    <div>
      {label && (
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          {label}
        </label>
      )}
      <input
        type="text"
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          block w-full px-4 py-3 border-2 rounded-lg text-right
          font-sans text-base
          transition-colors duration-200
          focus:ring-0 focus:border-blue-500 focus:outline-none
          disabled:bg-gray-100 disabled:text-gray-500
          ${error ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'}
          ${className}
        `}
      />
      {error && (
        <p className="mt-2 text-sm text-red-600">⚠️ {error}</p>
      )}
    </div>
  )
}
