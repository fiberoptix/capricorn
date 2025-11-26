/**
 * Modal Component - Standardized UI/UX
 * Reusable modal dialog with blue gradient header
 */

'use client'

import { useEffect, useRef } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  subtitle?: string
  icon?: React.ReactNode
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  variant?: 'primary' | 'success' | 'warning' | 'danger'
}

export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  children,
  size = 'md',
  className = '',
  variant = 'primary',
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Close modal when clicking backdrop
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  const gradientClasses = {
    primary: 'from-blue-600 to-blue-800',
    success: 'from-green-600 to-green-800',
    warning: 'from-amber-500 to-amber-700',
    danger: 'from-red-600 to-red-800',
  }

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      onClick={handleBackdropClick}
    >
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" />
        
        {/* Modal */}
        <div
          ref={modalRef}
          className={`
            relative w-full ${sizeClasses[size]} bg-white rounded-xl shadow-2xl
            transform transition-all animate-in fade-in zoom-in-95 duration-200 ${className}
          `}
        >
          {/* Header with gradient */}
          <div className={`
            flex items-center p-4 rounded-t-xl
            bg-gradient-to-r ${gradientClasses[variant]}
          `}>
            <div className="flex items-center gap-3">
              {icon && (
                <div className="p-2 bg-white/20 rounded-lg">
                  {icon}
                </div>
              )}
              <div>
                <h2 className="text-lg font-bold text-white">{title}</h2>
                {subtitle && (
                  <p className="text-sm text-white/80">{subtitle}</p>
                )}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-5">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

// Modal Footer Component
interface ModalFooterProps {
  children: React.ReactNode
  className?: string
}

export function ModalFooter({ children, className = '' }: ModalFooterProps) {
  return (
    <div className={`flex justify-end gap-3 pt-4 mt-4 border-t border-gray-200 ${className}`}>
      {children}
    </div>
  )
}
