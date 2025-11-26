/**
 * Taxes Module - Tax Comparison Dashboard
 * Shows your taxes based on Profile data with state comparison feature
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Paper,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  AccountBalance as TaxIcon,
  CompareArrows as CompareIcon,
  Home as HomeIcon,
  TrendingDown as SavingsIcon,
} from '@mui/icons-material';

import { API_V1_URL } from '../../config/api';

// API base URL (dynamic based on hostname)
const API_BASE = API_V1_URL;

// All US states with codes
const US_STATES = [
  { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' }, { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' }, { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' }, { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' }, { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' }, { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' }, { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' }, { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' }, { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' }, { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' }, { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' }, { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' }, { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' }, { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' }, { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' }, { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' }, { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' }, { code: 'DC', name: 'District of Columbia' }
];

// No income tax states
const NO_TAX_STATES = ['AK', 'FL', 'NV', 'SD', 'TX', 'WA', 'WY'];

interface TaxResult {
  gross_income: number;
  federal: {
    standard_deduction: number;
    taxable_income: number;
    tax: number;
    marginal_rate: number;
    effective_rate: number;
  };
  state: {
    state_code: string;
    standard_deduction: number;
    taxable_income: number;
    tax: number;
    marginal_rate: number;
    effective_rate: number;
  };
  local: {
    tax: number;
    rate: number;
  };
  total_tax: number;
  after_tax_income: number;
  effective_rate: number;
}

interface Profile {
  user_salary: number;
  partner_salary: number;
  user_bonus_rate: number;
  partner_bonus_rate: number;
  filing_status: string;
  state: string;
  local_tax_rate: number;
}

interface TaxCardData {
  state: string;
  stateName: string;
  result: TaxResult | null;
  error: string | null;
  loading: boolean;
  isHome: boolean;
  comparisonLabel?: string;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

const getStateName = (code: string): string => {
  return US_STATES.find(s => s.code === code)?.name || code;
};

const TaxComparisonCard: React.FC<{ 
  data: TaxCardData; 
  homeStateTax?: number;
}> = ({ data, homeStateTax }) => {
  const { state, stateName, result, error, loading, isHome, comparisonLabel } = data;
  const isNoTaxState = NO_TAX_STATES.includes(state);
  
  // Calculate savings compared to home state
  const savings = homeStateTax && result ? homeStateTax - result.total_tax : 0;
  const hasSavings = savings > 0;

  return (
    <Card 
      sx={{ 
        height: '100%',
        minHeight: 580,
        border: '3px solid',
        borderColor: isHome ? 'primary.main' : isNoTaxState ? 'success.main' : 'grey.400',
        transition: 'transform 0.2s, box-shadow 0.2s',
        position: 'relative',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
    >
      <CardContent sx={{ pt: 1 }}>
        {/* Label Badge - Now inside the card */}
        {(isHome || comparisonLabel) && (
          <Box
            sx={{
              display: 'inline-block',
              bgcolor: isHome ? 'primary.main' : 'grey.600',
              color: 'white',
              px: 2,
              py: 0.5,
              borderRadius: 1,
              fontSize: '0.75rem',
              fontWeight: 'bold',
              mb: 1.5,
            }}
          >
            {isHome ? '🏠 YOUR STATE' : comparisonLabel}
          </Box>
        )}
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isHome ? <HomeIcon color="primary" /> : <CompareIcon color="action" />}
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
              {stateName}
            </Typography>
          </Box>
          <Chip 
            label={state} 
            color={isNoTaxState ? 'success' : isHome ? 'primary' : 'default'} 
            size="small"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>

        {/* State Tax Badge - Always show */}
        {isNoTaxState ? (
          <Alert severity="success" sx={{ mb: 2, py: 0 }}>
            No State Income Tax! 🎉
          </Alert>
        ) : result && !loading ? (
          <Alert severity="info" sx={{ mb: 2, py: 0 }}>
            State Income Tax: {formatPercent(result.state.effective_rate)} effective
          </Alert>
        ) : null}

        {/* Loading State */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && (
          <Alert severity="error" sx={{ mt: 1 }}>
            {error}
          </Alert>
        )}

        {/* Results */}
        {result && !loading && (
          <Box>
            {/* Income */}
            <Box sx={{ mb: 2, p: 1.5, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                Total Household Income
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {formatCurrency(result.gross_income)}
              </Typography>
            </Box>

            <Divider sx={{ my: 1.5 }} />

            {/* Tax Breakdown */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {/* Federal */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body1">Federal Tax</Typography>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {formatCurrency(result.federal.tax)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatPercent(result.federal.effective_rate)} effective
                  </Typography>
                </Box>
              </Box>

              {/* State */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body1">
                  State Tax
                </Typography>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: result.state.tax === 0 ? 'success.main' : 'inherit'
                    }}
                  >
                    {result.state.tax === 0 ? '$0 ✓' : formatCurrency(result.state.tax)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatPercent(result.state.effective_rate)} effective
                  </Typography>
                </Box>
              </Box>

              {/* Local */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body1">Local Tax</Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatCurrency(result.local.tax)}
                </Typography>
              </Box>
            </Box>

            <Divider sx={{ my: 1.5 }} />

            {/* Total */}
            <Box sx={{ p: 1.5, bgcolor: 'primary.main', color: 'white', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  TOTAL TAX
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatCurrency(result.total_tax)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 0.5 }}>
                <Typography variant="caption" sx={{ opacity: 0.9 }}>
                  Effective Rate
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  {formatPercent(result.effective_rate)}
                </Typography>
              </Box>
            </Box>

            {/* After Tax Income */}
            <Box sx={{ mt: 2, p: 1.5, bgcolor: 'success.light', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ color: 'success.dark', fontWeight: 'medium' }}>
                  After-Tax Income
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.dark' }}>
                  {formatCurrency(result.after_tax_income)}
                </Typography>
              </Box>
            </Box>

            {/* Savings Comparison (only for comparison cards) */}
            {!isHome && homeStateTax !== undefined && (
              <Box 
                sx={{ 
                  mt: 2, 
                  p: 1.5, 
                  bgcolor: hasSavings ? 'success.main' : 'error.light', 
                  color: hasSavings ? 'white' : 'error.dark',
                  borderRadius: 1 
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SavingsIcon />
                  <Box>
                    <Typography variant="caption">
                      {hasSavings ? 'You would SAVE' : 'You would PAY MORE'}
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(Math.abs(savings))}/year
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export function TaxesModule() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [comparison1, setComparison1] = useState('FL');
  const [comparison2, setComparison2] = useState('TX');
  const [taxResults, setTaxResults] = useState<TaxCardData[]>([]);

  // Fetch profile on mount
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${API_BASE}/profile`);
        if (response.ok) {
          const data = await response.json();
          setProfile(data.profile);
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      } finally {
        setProfileLoading(false);
      }
    };
    fetchProfile();
  }, []);

  // Calculate taxes when profile or comparisons change
  useEffect(() => {
    if (!profile) return;

    const calculateTaxes = async () => {
      // Calculate total income (salary + bonus for both)
      const userBonus = profile.user_salary * (profile.user_bonus_rate || 0);
      const partnerBonus = (profile.partner_salary || 0) * (profile.partner_bonus_rate || 0);
      const totalIncome = profile.user_salary + (profile.partner_salary || 0) + userBonus + partnerBonus;

      const states = [
        { code: profile.state, isHome: true, label: undefined },
        { code: comparison1, isHome: false, label: 'COMPARISON 1' },
        { code: comparison2, isHome: false, label: 'COMPARISON 2' },
      ];

      // Initialize loading state
      setTaxResults(states.map(s => ({
        state: s.code,
        stateName: getStateName(s.code),
        result: null,
        error: null,
        loading: true,
        isHome: s.isHome,
        comparisonLabel: s.label,
      })));

      // Fetch all taxes
      const results = await Promise.all(
        states.map(async (s) => {
          try {
            // Use local tax only for home state
            const localTaxRate = s.isHome ? (profile.local_tax_rate || 0) : 0;
            
            const response = await fetch(`${API_BASE}/tax/income`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                income: totalIncome,
                filing_status: profile.filing_status,
                state: s.code,
                local_tax_rate: localTaxRate,
              }),
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            
            return {
              state: s.code,
              stateName: getStateName(s.code),
              result,
              error: null,
              loading: false,
              isHome: s.isHome,
              comparisonLabel: s.label,
            };
          } catch (err) {
            return {
              state: s.code,
              stateName: getStateName(s.code),
              result: null,
              error: err instanceof Error ? err.message : 'Unknown error',
              loading: false,
              isHome: s.isHome,
              comparisonLabel: s.label,
            };
          }
        })
      );

      setTaxResults(results);
    };

    calculateTaxes();
  }, [profile, comparison1, comparison2]);

  const homeStateTax = taxResults.find(r => r.isHome)?.result?.total_tax;

  if (profileLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!profile) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          Please set up your profile first to see your tax calculations.
        </Alert>
      </Box>
    );
  }

  const filingStatusDisplay = profile.filing_status
    ?.replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown';

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper 
        sx={{ 
          p: 3, 
          mb: 3, 
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          {/* Left: Title and info */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <TaxIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                Your Tax Exposure
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                {filingStatusDisplay} • {getStateName(profile.state)} | Compare states to see potential savings
              </Typography>
            </Box>
          </Box>

          {/* Right: Dropdowns */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Compare to</InputLabel>
            <Select
              value={comparison1}
              label="Compare to"
              onChange={(e) => setComparison1(e.target.value)}
              sx={{ 
                color: 'white',
                '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.8)' },
                '.MuiSvgIcon-root': { color: 'white' },
              }}
            >
              {US_STATES.filter(s => s.code !== profile.state && s.code !== comparison2).map((state) => (
                <MenuItem key={state.code} value={state.code}>
                  {state.name} ({state.code}) {NO_TAX_STATES.includes(state.code) && '✓ No Tax'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Compare to</InputLabel>
            <Select
              value={comparison2}
              label="Compare to"
              onChange={(e) => setComparison2(e.target.value)}
              sx={{ 
                color: 'white',
                '.MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.8)' },
                '.MuiSvgIcon-root': { color: 'white' },
              }}
            >
              {US_STATES.filter(s => s.code !== profile.state && s.code !== comparison1).map((state) => (
                <MenuItem key={state.code} value={state.code}>
                  {state.name} ({state.code}) {NO_TAX_STATES.includes(state.code) && '✓ No Tax'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          </Box>
        </Box>
      </Paper>

      {/* Tax Cards */}
      <Grid container spacing={3}>
        {taxResults.map((data, index) => (
          <Grid item xs={12} md={4} key={data.state + index}>
            <TaxComparisonCard 
              data={data} 
              homeStateTax={data.isHome ? undefined : homeStateTax}
            />
          </Grid>
        ))}
      </Grid>

      {/* Footer */}
      <Paper sx={{ mt: 3, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Calculations based on your Profile settings. Comparison states use 0% local tax. 
          No-tax states: AK, FL, NV, SD, TX, WA, WY.
        </Typography>
      </Paper>
    </Box>
  );
}

