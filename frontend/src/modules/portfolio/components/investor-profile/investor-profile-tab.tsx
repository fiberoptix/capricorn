'use client'

import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { 
  User, 
  DollarSign, 
  MapPin, 
  Save, 
  Edit,
  CheckCircle,
  AlertCircle,
  X
} from 'lucide-react'
import { 
  usePrimaryInvestorProfile,
  useUpdateInvestorProfile,
  InvestorProfileUpdate 
} from '../../hooks/use-investor-profiles'
import { api } from '../../lib/api-client'

// Filing status options
const FILING_STATUS_OPTIONS = [
  { value: 'single', label: 'Single' },
  { value: 'married_filing_jointly', label: 'Married Filing Jointly' },
  { value: 'married_filing_separately', label: 'Married Filing Separately' },
  { value: 'head_of_household', label: 'Head of Household' },
]

// US State options (abbreviated list)
const STATE_OPTIONS = [
  { value: 'AL', label: 'Alabama' },
  { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' },
  { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' },
  { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' },
  { value: 'DE', label: 'Delaware' },
  { value: 'FL', label: 'Florida' },
  { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' },
  { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' },
  { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' },
  { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' },
  { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' },
  { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' },
  { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' },
  { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' },
  { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' },
  { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' },
  { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' },
  { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' },
  { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' },
  { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' },
  { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' },
  { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' },
  { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' },
  { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' },
  { value: 'WY', label: 'Wyoming' },
]

export function InvestorProfileTab() {
  const { data: profile, isLoading, error } = usePrimaryInvestorProfile()
  const updateProfile = useUpdateInvestorProfile()
  const queryClient = useQueryClient()
  
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<InvestorProfileUpdate>({})
  
  // Initialize form data when profile loads
  useEffect(() => {
    if (profile) {
      setFormData({
        name: profile.name || '',
        annual_household_income: profile.annual_household_income || 0,
        filing_status: profile.filing_status || 'married_filing_jointly',
        state_of_residence: profile.state_of_residence || '',
        local_tax_rate: (profile.local_tax_rate || 0) * 100, // Convert to percentage for display
      })
    }
  }, [profile])
  
  const handleSave = async () => {
    if (!profile) return
    
    try {
      // Convert local_tax_rate back to decimal
      const updateData = {
        ...formData,
        local_tax_rate: (formData.local_tax_rate || 0) / 100,
      }
      
      // Execute mutation (always updates profile ID 1 - single profile system)
      await updateProfile.mutateAsync({ 
        profileId: 1,  // Hardcoded: single-profile system always uses ID 1
        data: updateData 
      })
      
      // CRITICAL: Explicitly refetch profile ID 1 before closing edit mode
      await queryClient.refetchQueries({ 
        queryKey: ['investor-profiles', 1],
        type: 'active'
      })
      
      // Now safe to close edit mode - data is fresh
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update profile:', error)
    }
  }
  
  const handleCancel = () => {
    // Reset form data to original profile values
    if (profile) {
      setFormData({
        name: profile.name || '',
        annual_household_income: profile.annual_household_income || 0,
        filing_status: profile.filing_status || 'married_filing_jointly',
        state_of_residence: profile.state_of_residence || '',
        local_tax_rate: (profile.local_tax_rate || 0) * 100,
      })
    }
    setIsEditing(false)
  }
  
  // Format currency for display
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }
  
  // Get filing status label
  const getFilingStatusLabel = (status: string) => {
    return FILING_STATUS_OPTIONS.find(opt => opt.value === status)?.label || status
  }
  
  // Get state label
  const getStateLabel = (state: string) => {
    return STATE_OPTIONS.find(opt => opt.value === state)?.label || state
  }
  
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold">Investor Profile</h2>
          <p className="text-gray-600">Personal information and tax configuration</p>
        </div>
        <div className="text-center py-12">
          <p className="text-gray-500">Loading profile...</p>
        </div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold">Investor Profile</h2>
          <p className="text-gray-600">Personal information and tax configuration</p>
        </div>
        <div className="text-center py-12">
          <AlertCircle className="h-16 w-16 mx-auto mb-4 text-red-400" />
          <p className="text-lg text-red-600">Error loading profile</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    )
  }
  
  if (!profile) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold">Investor Profile</h2>
          <p className="text-gray-600">Personal information and tax configuration</p>
        </div>
        <div className="text-center py-12">
          <User className="h-16 w-16 mx-auto mb-4 text-gray-400" />
          <p className="text-lg text-gray-600">No profile found</p>
          <p className="text-sm text-gray-500 mt-2">Create a profile to get started</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Investor Profile</h2>
              <p className="text-gray-600">Personal information and tax configuration</p>
            </div>
            <div className="flex items-center space-x-2">
              {/* Data Export/Import Controls */}
              <div className="flex items-center space-x-2 mr-3">
                <button
                  onClick={async () => {
                    try {
                      // Fetch portfolios first, then gather transactions per portfolio
                      const portfoliosResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/portfolios`)
                      const portfoliosJson = portfoliosResp.ok ? await portfoliosResp.json() : { portfolios: [] }
                      const portfoliosArr = Array.isArray(portfoliosJson.portfolios) ? portfoliosJson.portfolios : []

                      // Gather transactions for each portfolio and tag with portfolio_name
                      const allTransactions: any[] = []
                      for (const p of portfoliosArr) {
                        try {
                          const txResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/transactions?portfolio_id=${p.id}`)
                          if (txResp.ok) {
                            const txJson = await txResp.json()
                            const txs = Array.isArray(txJson.transactions) ? txJson.transactions : []
                            for (const t of txs) {
                              allTransactions.push({ ...t, portfolio_name: p.name })
                            }
                          }
                        } catch {}
                      }

                      // Investor profiles
                      const profilesResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/investor-profiles`)
                      const profilesJson = profilesResp.ok ? await profilesResp.json() : { profiles: [] }

                      // Market prices
                      const pricesResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/market-prices`)
                      const pricesJson = pricesResp.ok ? await pricesResp.json() : { prices: [] }

                      const blob = new Blob([
                        JSON.stringify({
                          exported_at: new Date().toISOString(),
                          profiles: profilesJson.profiles ?? [],
                          portfolios: portfoliosArr ?? [],
                          transactions: allTransactions,
                          prices: pricesJson.prices ?? [],
                        }, null, 2)
                      ], { type: 'application/json' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      const now = new Date()
                      const pad = (n: number) => n.toString().padStart(2, '0')
                      const yyyy = now.getFullYear()
                      const mm = pad(now.getMonth() + 1)
                      const dd = pad(now.getDate())
                      const hh = pad(now.getHours())
                      const mi = pad(now.getMinutes())
                      a.download = `Portfolio_Manager_BAK_${yyyy}-${mm}-${dd}_${hh}${mi}.json`
                      document.body.appendChild(a)
                      a.click()
                      a.remove()
                      URL.revokeObjectURL(url)
                    } catch (e) {
                      console.error('Export failed', e)
                    }
                  }}
                  className="btn btn-secondary"
                >
                  Export Portfolio Data
                </button>
                <label className="btn btn-secondary cursor-pointer">
                  Import Portfolio Data
                  <input
                    type="file"
                    accept="application/json"
                    className="hidden"
                    onChange={async (e) => {
                      const file = e.target.files?.[0]
                      if (!file) return
                      try {
                        const text = await file.text()
                        const data = JSON.parse(text)
                        // Profiles: create first profile if provided
                        if (Array.isArray(data.profiles) && data.profiles.length > 0) {
                          const p = data.profiles[0]
                          await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/investor-profiles`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              name: p.name || 'Primary',
                              household_income: p.household_income ?? p.annual_household_income ?? 0,
                              filing_status: p.filing_status || 'married_joint',
                              state_of_residence: p.state_of_residence || 'NY',
                              local_tax_rate: p.local_tax_rate ?? 0
                            })
                          }).catch(() => null)
                        }

                        // Get existing portfolios for name collision detection
                        const portfoliosResp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/portfolios`)
                        const existingPortfolios = portfoliosResp.ok ? (await portfoliosResp.json()).portfolios || [] : []
                        const existingNames = existingPortfolios.map((p: any) => p.name)
                        
                        // Create portfolios with collision-safe names and map original name -> new id
                        const originalNameToNewId: Record<string, number> = {}
                        if (Array.isArray(data.portfolios)) {
                          for (const pf of data.portfolios) {
                            try {
                              // Handle name collisions with date suffix
                              let finalName = pf.name
                              if (existingNames.includes(pf.name)) {
                                const today = new Date()
                                const dateStr = `${today.getFullYear()}.${(today.getMonth() + 1)}.${today.getDate()}`
                                finalName = `${pf.name} ${dateStr}`
                                console.log(`Portfolio name collision: '${pf.name}' -> '${finalName}'`)
                              }
                              
                              const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/portfolios`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ name: finalName, type: pf.type, description: pf.description, cash_on_hand: pf.cash_on_hand ?? 0.00 })
                              })
                              if (resp.ok) {
                                const created = await resp.json()
                                if (created?.id && pf?.name) {
                                  originalNameToNewId[pf.name] = created.id
                                  console.log(`Created portfolio: '${finalName}' (ID: ${created.id})`)
                                }
                              }
                            } catch (e) {
                              console.error(`Failed to create portfolio ${pf.name}:`, e)
                            }
                          }
                        }

                        // Transactions FIRST (use original portfolio name mapping to new IDs)
                        if (Array.isArray(data.transactions)) {
                          for (const tx of data.transactions) {
                            // Map transactions to newly created portfolios by original name
                            const pid = tx.portfolio_name ? originalNameToNewId[tx.portfolio_name] : undefined
                            if (!pid) {
                              console.warn(`Skipping transaction ${tx.ticker}: no portfolio mapping for '${tx.portfolio_name}'`)
                              continue
                            }
                            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/transactions`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                portfolio_id: pid,
                                ticker: tx.ticker,
                                transaction_type: tx.transaction_type,
                                quantity: tx.quantity,
                                price_per_share: tx.price_per_share,
                                transaction_date: tx.transaction_date,
                                stock_name: tx.stock_name
                              })
                            }).catch(() => null)
                          }
                        }

                        // Prices LAST (override any $0.01 defaults created by transactions)
                        if (Array.isArray(data.prices)) {
                          for (const pr of data.prices) {
                            if (!pr?.ticker || pr.current_price === undefined) continue
                            await fetch(`${process.env.NEXT_PUBLIC_API_URL || '/api/backend'}/api/market-prices/${pr.ticker}`, {
                              method: 'PUT',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ current_price: pr.current_price })
                            }).catch(() => null)
                          }
                        }
                        // Refresh page state
                        window.location.reload()
                      } catch (err) {
                        console.error('Import failed', err)
                      } finally {
                        e.currentTarget.value = ''
                      }
                    }}
                  />
                </label>
              </div>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn btn-primary inline-flex items-center"
                >
                  <Edit className="h-4 w-4 mr-2" />
                  <span>Edit Profile</span>
                </button>
              ) : (
                <>
                  <button
                    onClick={handleCancel}
                    className="btn btn-secondary"
                    disabled={updateProfile.isPending}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="btn btn-primary"
                    disabled={updateProfile.isPending}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {updateProfile.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* Success Message */}
        {updateProfile.isSuccess && !isEditing && (
          <div className="mx-6 mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-sm text-green-700">Profile updated successfully!</p>
            </div>
          </div>
        )}
        
        {/* Profile Form/Display */}
        <div className="space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <User className="h-5 w-5 mr-2 text-blue-600" />
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="input"
                    placeholder="Enter full name"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md border">
                    {profile.name || 'Not specified'}
                  </div>
                )}
              </div>

            </div>
          </div>
          
          {/* Financial Information */}
          <div>
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <DollarSign className="h-5 w-5 mr-2 text-green-600" />
              Financial Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Household Income
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    value={formData.annual_household_income || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, annual_household_income: parseFloat(e.target.value) || 0 }))}
                    className="input"
                    placeholder="350000"
                    min="0"
                    step="1000"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md border">
                    {formatCurrency(profile.annual_household_income || 0)}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filing Status
                </label>
                {isEditing ? (
                  <select
                    value={formData.filing_status || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, filing_status: e.target.value as 'single' | 'married_filing_jointly' | 'married_filing_separately' | 'head_of_household' }))}
                    className="input"
                  >
                    {FILING_STATUS_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md border">
                    {getFilingStatusLabel(profile.filing_status || '')}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Location & Tax Information */}
          <div>
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <MapPin className="h-5 w-5 mr-2 text-red-600" />
              Location & Tax Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  State of Residence
                </label>
                {isEditing ? (
                  <select
                    value={formData.state_of_residence || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, state_of_residence: e.target.value }))}
                    className="input"
                  >
                    <option value="">Select a state</option>
                    {STATE_OPTIONS.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md border">
                    {getStateLabel(profile.state_of_residence || '')}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Local Tax Rate (%)
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    value={formData.local_tax_rate || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, local_tax_rate: parseFloat(e.target.value) || 0 }))}
                    className="input"
                    placeholder="1.0"
                    min="0"
                    max="20"
                    step="0.1"
                  />
                ) : (
                  <div className="p-3 bg-gray-50 rounded-md border">
                    {((profile.local_tax_rate || 0) * 100).toFixed(1)}%
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}