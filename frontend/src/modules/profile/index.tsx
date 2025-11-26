/**
 * Profile Module - Standardized UI/UX
 * Single source of truth for all user financial/personal data
 * Matches TAXES/TEST UI style
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Grid,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useProfile, useUpdateProfile } from './hooks/use-profile';
import { ProfileUpdateRequest } from './types/profile.types';

// US States for dropdown
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

const FILING_STATUS_OPTIONS = [
  { value: 'single', label: 'Single' },
  { value: 'married_filing_jointly', label: 'Married Filing Jointly' },
  { value: 'married_filing_separately', label: 'Married Filing Separately' },
  { value: 'head_of_household', label: 'Head of Household' },
];

// Section Card Component - Standardized style
interface SectionCardProps {
  title: string;
  emoji: string;
  children: React.ReactNode;
  note?: React.ReactNode;
}

const SectionCard: React.FC<SectionCardProps> = ({ title, emoji, children, note }) => (
  <Card sx={{ mb: 2 }}>
    <CardContent sx={{ p: 2 }}>
      <Box sx={{ 
        display: 'inline-block',
        bgcolor: 'primary.main',
        color: 'white',
        px: 2,
        py: 0.5,
        borderRadius: 1,
        fontSize: '0.85rem',
        fontWeight: 'bold',
        mb: 2,
      }}>
        {emoji} {title}
      </Box>
      {children}
      {note && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="caption" color="text.secondary">
            {note}
          </Typography>
        </>
      )}
    </CardContent>
  </Card>
);

export function ProfileModule() {
  const { data: profile, isLoading, error } = useProfile();
  const updateProfile = useUpdateProfile();

  // Local state for form data
  const [formData, setFormData] = useState<ProfileUpdateRequest>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Initialize form data when profile loads
  useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  // Handle field changes
  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setSaveStatus('idle');
  };

  // Handle save
  const handleSave = async () => {
    try {
      await updateProfile.mutateAsync(formData);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (err) {
      setSaveStatus('error');
      console.error('Failed to save profile:', err);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load profile: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Header - Blue gradient like TAXES */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 3, 
          mb: 3, 
          background: 'linear-gradient(135deg, #1976d2 0%, #0d47a1 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PersonIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                Profile Settings
              </Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                Single source of truth for all your personal and financial data
              </Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={updateProfile.isPending}
            sx={{ 
              bgcolor: 'white', 
              color: 'primary.main',
              '&:hover': { bgcolor: 'grey.100' }
            }}
          >
            {updateProfile.isPending ? 'Saving...' : 'Save All Changes'}
          </Button>
        </Box>
      </Paper>

      {/* Save Status Alert */}
      {saveStatus === 'success' && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Profile updated successfully! Portfolio and Retirement modules will use this data.
        </Alert>
      )}
      {saveStatus === 'error' && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to update profile. Please try again.
        </Alert>
      )}

      {/* Main Content - 2 Column Layout */}
      <Grid container spacing={2}>
        {/* Left Column */}
        <Grid item xs={12} md={6}>
          {/* Personal Information */}
          <SectionCard title="Personal Information" emoji="👥">
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Primary Person"
                  value={formData.user || ''}
                  onChange={(e) => handleChange('user', e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner"
                  value={formData.partner || ''}
                  onChange={(e) => handleChange('partner', e.target.value)}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's Age"
                  type="number"
                  value={formData.user_age || 0}
                  onChange={(e) => handleChange('user_age', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's Age"
                  type="number"
                  value={formData.partner_age || 0}
                  onChange={(e) => handleChange('partner_age', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="User Yrs to Retire"
                  type="number"
                  value={formData.user_years_to_retirement || 0}
                  onChange={(e) => handleChange('user_years_to_retirement', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner Yrs to Retire"
                  type="number"
                  value={formData.partner_years_to_retirement || 0}
                  onChange={(e) => handleChange('partner_years_to_retirement', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Retirement Duration"
                  type="number"
                  value={formData.years_of_retirement || 30}
                  onChange={(e) => handleChange('years_of_retirement', parseInt(e.target.value))}
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Income Parameters */}
          <SectionCard title="Income Parameters" emoji="💼">
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's Salary"
                  type="number"
                  value={formData.user_salary || 0}
                  onChange={(e) => handleChange('user_salary', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's Salary"
                  type="number"
                  value={formData.partner_salary || 0}
                  onChange={(e) => handleChange('partner_salary', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's Bonus Rate"
                  type="number"
                  value={(formData.user_bonus_rate || 0) * 100}
                  onChange={(e) => handleChange('user_bonus_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's Bonus Rate"
                  type="number"
                  value={(formData.partner_bonus_rate || 0) * 100}
                  onChange={(e) => handleChange('partner_bonus_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's Raise Rate"
                  type="number"
                  value={(formData.user_raise_rate || 0) * 100}
                  onChange={(e) => handleChange('user_raise_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's Raise Rate"
                  type="number"
                  value={(formData.partner_raise_rate || 0) * 100}
                  onChange={(e) => handleChange('partner_raise_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Expense Parameters */}
          <SectionCard 
            title="Expense Parameters" 
            emoji="🏠"
            note={<><strong>Essential:</strong> Housing, utilities, food, insurance. <strong>Discretionary:</strong> Travel, entertainment, hobbies.</>}
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Monthly Living Expenses"
                  type="number"
                  value={formData.monthly_living_expenses || 0}
                  onChange={(e) => handleChange('monthly_living_expenses', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Annual Discretionary"
                  type="number"
                  value={formData.annual_discretionary_spending || 0}
                  onChange={(e) => handleChange('annual_discretionary_spending', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="Annual Inflation Rate"
                  type="number"
                  value={(formData.annual_inflation_rate || 0) * 100}
                  onChange={(e) => handleChange('annual_inflation_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Tax Parameters */}
          <SectionCard 
            title="Tax Parameters" 
            emoji="🏛️"
            note="Uses 2025 federal and state tax brackets. Effective rates calculated automatically."
          >
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  size="small"
                  select
                  label="State"
                  value={formData.state || 'NY'}
                  onChange={(e) => handleChange('state', e.target.value)}
                >
                  {US_STATES.map((state) => (
                    <MenuItem key={state.code} value={state.code}>
                      {state.name} ({state.code})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={5}>
                <TextField
                  fullWidth
                  size="small"
                  select
                  label="Filing Status"
                  value={formData.filing_status || 'married_filing_jointly'}
                  onChange={(e) => handleChange('filing_status', e.target.value)}
                >
                  {FILING_STATUS_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={3}>
                <TextField
                  fullWidth
                  size="small"
                  label="Local Tax"
                  type="number"
                  value={(formData.local_tax_rate || 0) * 100}
                  onChange={(e) => handleChange('local_tax_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
            </Grid>
          </SectionCard>
        </Grid>

        {/* Right Column */}
        <Grid item xs={12} md={6}>
          {/* 401K Parameters */}
          <SectionCard 
            title="401K Parameters" 
            emoji="🏦"
            note={<><strong>💡 Tip:</strong> S&P 500 has averaged ~10% annual returns over 30-year periods.</>}
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's 401K Contribution"
                  type="number"
                  value={formData.user_401k_contribution || 0}
                  onChange={(e) => handleChange('user_401k_contribution', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's 401K Contribution"
                  type="number"
                  value={formData.partner_401k_contribution || 0}
                  onChange={(e) => handleChange('partner_401k_contribution', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's Employer Match"
                  type="number"
                  value={formData.user_employer_match || 0}
                  onChange={(e) => handleChange('user_employer_match', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's Employer Match"
                  type="number"
                  value={formData.partner_employer_match || 0}
                  onChange={(e) => handleChange('partner_employer_match', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's 401K Balance"
                  type="number"
                  value={formData.user_current_401k_balance || 0}
                  onChange={(e) => handleChange('user_current_401k_balance', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's 401K Balance"
                  type="number"
                  value={formData.partner_current_401k_balance || 0}
                  onChange={(e) => handleChange('partner_current_401k_balance', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="User's 401K Growth"
                  type="number"
                  value={(formData.user_401k_growth_rate || 0) * 100}
                  onChange={(e) => handleChange('user_401k_growth_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Partner's 401K Growth"
                  type="number"
                  value={(formData.partner_401k_growth_rate || 0) * 100}
                  onChange={(e) => handleChange('partner_401k_growth_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Investment Accounts */}
          <SectionCard title="Investment Accounts" emoji="📈">
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="IRA Balance"
                  type="number"
                  value={formData.current_ira_balance || 0}
                  onChange={(e) => handleChange('current_ira_balance', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="IRA Return Rate"
                  type="number"
                  value={(formData.ira_return_rate || 0) * 100}
                  onChange={(e) => handleChange('ira_return_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Trading Account Balance"
                  type="number"
                  value={formData.current_trading_balance || 0}
                  onChange={(e) => handleChange('current_trading_balance', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Trading Return Rate"
                  type="number"
                  value={(formData.trading_return_rate || 0) * 100}
                  onChange={(e) => handleChange('trading_return_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Expected Inheritance"
                  type="number"
                  value={formData.expected_inheritance || 0}
                  onChange={(e) => handleChange('expected_inheritance', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Inheritance Year"
                  type="number"
                  value={formData.inheritance_year || 20}
                  onChange={(e) => handleChange('inheritance_year', parseInt(e.target.value))}
                  helperText="Years from now"
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Retirement Parameters */}
          <SectionCard 
            title="Retirement Parameters" 
            emoji="🎯"
            note={<><strong>💡 Strategy:</strong> 5% growth = conservative retirement investments. 4% withdrawal = sustainable income rule.</>}
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Retirement Growth Rate"
                  type="number"
                  value={(formData.retirement_growth_rate || 0) * 100}
                  onChange={(e) => handleChange('retirement_growth_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Withdrawal Rate (4% Rule)"
                  type="number"
                  value={(formData.withdrawal_rate || 0) * 100}
                  onChange={(e) => handleChange('withdrawal_rate', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
            </Grid>
          </SectionCard>

          {/* Savings Strategy */}
          <SectionCard 
            title="Savings Strategy" 
            emoji="💲"
            note="Annual savings accumulate and transfer to your chosen destination at year-end."
          >
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Fixed Monthly Savings"
                  type="number"
                  value={formData.fixed_monthly_savings || 0}
                  onChange={(e) => handleChange('fixed_monthly_savings', parseFloat(e.target.value))}
                  InputProps={{ startAdornment: <Typography sx={{ mr: 0.5 }}>$</Typography> }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="% of Leftover Money"
                  type="number"
                  value={(formData.percentage_of_leftover || 0) * 100}
                  onChange={(e) => handleChange('percentage_of_leftover', parseFloat(e.target.value) / 100)}
                  InputProps={{ endAdornment: <Typography sx={{ ml: 0.5 }}>%</Typography> }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  select
                  label="Annual Savings Destination"
                  value={formData.savings_destination || 'trading'}
                  onChange={(e) => handleChange('savings_destination', e.target.value)}
                >
                  <MenuItem value="savings">Keep in Savings (0% growth, liquid)</MenuItem>
                  <MenuItem value="trading">Transfer to Trading (investment growth)</MenuItem>
                </TextField>
              </Grid>
            </Grid>
          </SectionCard>
        </Grid>
      </Grid>

      {/* Footer Note */}
      <Paper sx={{ mt: 3, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> All data is saved to your profile and used by Portfolio, Retirement, and Taxes modules for calculations.
        </Typography>
      </Paper>
    </Box>
  );
}
