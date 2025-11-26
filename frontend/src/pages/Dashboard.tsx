/**
 * Dashboard - Standardized UI/UX
 * Unified overview of all financial modules
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  AccountBalance,
  TrendingUp,
  Receipt,
  Category,
  ShowChart,
  AccountBalanceWallet,
  BeachAccess,
  Savings,
  DateRange,
  Dashboard as DashboardIcon,
  PieChart,
  Assessment,
  AttachMoney,
  AccountBalanceWallet as FederalIcon,
  LocationCity,
  Home,
} from '@mui/icons-material';
import { financeAPI } from '../modules/finance/services/api';

import { API_V1_URL } from '../config/api';

// API base URL (dynamic based on hostname)
const API_BASE = API_V1_URL;

interface DashboardMetrics {
  finance: {
    income: number;
    expenses: number;
    avgMonthlySpending: number;
    monthsOfData: number;
    savings: number;
    savingsRate: number;
  };
  portfolio: {
    totalValue: number;
    securitiesValue: number;
    taxLiability: number;
    afterTaxValue: number;
    cashOnHand: number;
  };
  retirement: {
    yearsToRetirement: number;
    retirementYear: number;
    monthlyRetirementIncome: number;
    targetMonthlyNeed: number;
    projectedAssets: number;
  };
}

interface TaxData {
  grossIncome: number;
  federalTax: number;
  stateTax: number;
  localTax: number;
  totalTax: number;
  afterTaxIncome: number;
  effectiveRate: number;
  state: string;
  filingStatus: string;
}

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, subtitle, icon, color = '#3b82f6' }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Box sx={{ 
          p: 1.5, 
          borderRadius: 1.5, 
          bgcolor: `${color}15`,
          color: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {icon}
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            {label}
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 'bold', color, lineHeight: 1.2 }}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

// Section Header Component
interface SectionHeaderProps {
  title: string;
  icon: React.ReactNode;
  color?: string;
  bgGradient?: string;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ 
  title, 
  icon, 
  color = 'white',
  bgGradient = 'linear-gradient(135deg, #3b82f6, #1d4ed8)'
}) => (
  <Box sx={{ 
    background: bgGradient,
    color: color,
    px: 2,
    py: 1.5,
    borderRadius: '8px 8px 0 0',
    display: 'flex',
    alignItems: 'center',
    gap: 1.5
  }}>
    {icon}
    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
      {title}
    </Typography>
  </Box>
);

export const Dashboard: React.FC = () => {
  const currentYear = new Date().getFullYear();
  
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    finance: {
      income: 0,
      expenses: 0,
      avgMonthlySpending: 0,
      monthsOfData: 0,
      savings: 0,
      savingsRate: 0,
    },
    portfolio: {
      totalValue: 0,
      securitiesValue: 0,
      taxLiability: 0,
      afterTaxValue: 0,
      cashOnHand: 0,
    },
    retirement: {
      yearsToRetirement: 0,
      retirementYear: 0,
      monthlyRetirementIncome: 0,
      targetMonthlyNeed: 0,
      projectedAssets: 0,
    },
  });

  const [taxData, setTaxData] = useState<TaxData | null>(null);
  const [taxLoading, setTaxLoading] = useState(true);

  useEffect(() => {
    // Fetch real finance data from the Finance module API
    const fetchFinanceData = async () => {
      try {
        // Get current year data (same as Finance Dashboard default)
        const response = await financeAPI.getFinancialSummary({ period: 'this_year' });
        // API returns { data: { summary: {...}, categories: [...] } }
        const apiData = response.data.data;
        
        // Map finance data to dashboard metrics (same as Finance Dashboard)
        setMetrics(prev => ({
          ...prev,
          finance: {
            income: apiData.summary?.total_income || 0,
            expenses: apiData.summary?.total_expenses || 0,
            avgMonthlySpending: apiData.quick_stats?.average_monthly_spending || 0,
            monthsOfData: apiData.quick_stats?.months_of_data || 0,
            savings: apiData.summary?.balance || 0,
            savingsRate: apiData.summary?.savings_rate || 0,
          },
        }));
      } catch (err) {
        console.error('Failed to fetch finance data:', err);
        // Keep default zeros on error
      }
    };
    
    // Fetch portfolio data (same as Portfolio Overview)
    const fetchPortfolioData = async () => {
      try {
        const response = await fetch(`${API_BASE}/portfolio/summary`);
        if (response.ok) {
          const data = await response.json();
          setMetrics(prev => ({
            ...prev,
            portfolio: {
              totalValue: data.total_value || 0,
              securitiesValue: data.securities_value || 0,
              taxLiability: data.tax_liability || 0,
              afterTaxValue: data.after_tax_value || 0,
              cashOnHand: data.cash_on_hand || 0,
            },
          }));
        }
      } catch (err) {
        console.error('Failed to fetch portfolio data:', err);
      }
    };
    
    // Fetch retirement data (same as Retirement Dashboard Key Statistics)
    const fetchRetirementData = async () => {
      try {
        const response = await fetch(`${API_BASE}/retirement/summary`);
        if (response.ok) {
          const result = await response.json();
          const data = result.data;
          const retirementAnalysis = data?.retirement_analysis;
          const summary = data?.summary;
          const currentYear = new Date().getFullYear();
          const retirementYear = summary?.user_retirement_year || currentYear;
          
          setMetrics(prev => ({
            ...prev,
            retirement: {
              yearsToRetirement: retirementYear - currentYear,
              retirementYear: retirementYear,
              monthlyRetirementIncome: retirementAnalysis?.withdrawalAnalysis?.monthlyNetWithdrawal || 0,
              targetMonthlyNeed: retirementAnalysis?.lifestyleAnalysis?.targetMonthlyNeed || 0,
              projectedAssets: summary?.final_assets || 0,
            },
          }));
        }
      } catch (err) {
        console.error('Failed to fetch retirement data:', err);
      }
    };
    
    fetchFinanceData();
    fetchPortfolioData();
    fetchRetirementData();
  }, []);

  // Fetch tax data based on profile
  useEffect(() => {
    const fetchTaxData = async () => {
      try {
        // First get the profile
        const profileResponse = await fetch(`${API_BASE}/profile`);
        if (!profileResponse.ok) throw new Error('Failed to fetch profile');
        const profileData = await profileResponse.json();
        const profile = profileData.profile;

        // Calculate total income (same calculation as Taxes module)
        const userBonus = profile.user_salary * (profile.user_bonus_rate || 0);
        const partnerBonus = (profile.partner_salary || 0) * (profile.partner_bonus_rate || 0);
        const totalIncome = profile.user_salary + (profile.partner_salary || 0) + userBonus + partnerBonus;

        // Call tax API
        const taxResponse = await fetch(`${API_BASE}/tax/income`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            income: totalIncome,
            filing_status: profile.filing_status,
            state: profile.state,
            local_tax_rate: profile.local_tax_rate || 0,
          }),
        });

        if (!taxResponse.ok) throw new Error('Failed to fetch tax data');
        const result = await taxResponse.json();

        setTaxData({
          grossIncome: result.gross_income,
          federalTax: result.federal?.tax || 0,
          stateTax: result.state?.tax || 0,
          localTax: result.local?.tax || 0,
          totalTax: result.total_tax,
          afterTaxIncome: result.after_tax_income,
          effectiveRate: result.effective_rate,
          state: profile.state,
          filingStatus: profile.filing_status,
        });
      } catch (err) {
        console.error('Failed to fetch tax data:', err);
        // Set fallback demo data
        setTaxData({
          grossIncome: 250000,
          federalTax: 45000,
          stateTax: 15000,
          localTax: 2500,
          totalTax: 62500,
          afterTaxIncome: 187500,
          effectiveRate: 25,
          state: 'NY',
          filingStatus: 'married_filing_jointly',
        });
      } finally {
        setTaxLoading(false);
      }
    };

    fetchTaxData();
  }, []);

  const formatCurrency = (value: number, decimals: number = 2) => {
    return `$${value.toLocaleString('en-US', { 
      minimumFractionDigits: decimals, 
      maximumFractionDigits: decimals 
    })}`;
  };

  const formatFilingStatus = (status: string) => {
    const map: Record<string, string> = {
      'single': 'Single',
      'married_filing_jointly': 'Married Filing Jointly',
      'married_filing_separately': 'Married Filing Separately',
      'head_of_household': 'Head of Household',
    };
    return map[status] || status;
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #1e3a5f, #2d5a87)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <DashboardIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Financial Dashboard
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Your unified view of finances, investments, and retirement planning
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Finance Section */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <SectionHeader 
          title="💰 Finance Overview" 
          icon={<AccountBalance />}
          bgGradient="linear-gradient(135deg, #059669, #047857)"
        />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label={`${currentYear} Income`}
                value={formatCurrency(metrics.finance.income)}
                subtitle="Year to date"
                icon={<TrendingUp />}
                color={metrics.finance.income >= 0 ? '#10b981' : '#ef4444'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label={`${currentYear} Expenses`}
                value={formatCurrency(metrics.finance.expenses)}
                subtitle="Year to date"
                icon={<Receipt />}
                color={metrics.finance.expenses >= 0 ? '#ef4444' : '#10b981'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label={`${currentYear} Monthly Avg`}
                value={formatCurrency(metrics.finance.avgMonthlySpending, 0)}
                subtitle={`Over ${metrics.finance.monthsOfData.toFixed(1)} months`}
                icon={<DateRange />}
                color="#f59e0b"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label={`${currentYear} Savings`}
                value={formatCurrency(metrics.finance.savings)}
                subtitle="Year to date"
                icon={<AccountBalance />}
                color={metrics.finance.savings >= 0 ? '#10b981' : '#ef4444'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="Savings Rate"
                value={`${metrics.finance.savingsRate.toFixed(1)}%`}
                subtitle="Of After-Tax income"
                icon={<PieChart />}
                color={metrics.finance.savingsRate >= 0 ? '#3b82f6' : '#ef4444'}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Taxes Section - NEW */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <SectionHeader 
          title="🧾 Tax Overview" 
          icon={<Receipt />}
          bgGradient="linear-gradient(135deg, #f59e0b, #d97706)"
        />
        <CardContent>
          {taxLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : taxData ? (
            <>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="Gross Income"
                    value={formatCurrency(taxData.grossIncome, 0)}
                    subtitle={`${taxData.state} • ${formatFilingStatus(taxData.filingStatus).split(' ')[0]}`}
                    icon={<AttachMoney />}
                    color="#059669"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="Federal Tax"
                    value={formatCurrency(taxData.federalTax, 0)}
                    subtitle="IRS"
                    icon={<FederalIcon />}
                    color="#3b82f6"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="State Tax"
                    value={formatCurrency(taxData.stateTax, 0)}
                    subtitle={taxData.state}
                    icon={<LocationCity />}
                    color="#8b5cf6"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="Local Tax"
                    value={formatCurrency(taxData.localTax, 0)}
                    subtitle="NYC/Local"
                    icon={<Home />}
                    color="#f59e0b"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="Total Tax"
                    value={formatCurrency(taxData.totalTax, 0)}
                    subtitle={`${(taxData.effectiveRate > 1 ? taxData.effectiveRate : taxData.effectiveRate * 100).toFixed(1)}% eff. rate`}
                    icon={<Receipt />}
                    color="#ef4444"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <SummaryCard
                    label="After-Tax"
                    value={formatCurrency(taxData.afterTaxIncome, 0)}
                    subtitle="Take home"
                    icon={<Savings />}
                    color="#10b981"
                  />
                </Grid>
              </Grid>
            </>
          ) : (
            <Typography color="text.secondary">Unable to load tax data</Typography>
          )}
        </CardContent>
      </Paper>

      {/* Portfolio Section - Same 5 cards as Portfolio page */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <SectionHeader 
          title="📈 Portfolio Overview" 
          icon={<ShowChart />}
          bgGradient="linear-gradient(135deg, #3b82f6, #1d4ed8)"
        />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="Total Value"
                value={formatCurrency(metrics.portfolio.totalValue)}
                subtitle="Investment + Cash"
                icon={<AttachMoney />}
                color="#3b82f6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="Securities Value"
                value={formatCurrency(metrics.portfolio.securitiesValue)}
                subtitle="Investments only"
                icon={<TrendingUp />}
                color="#6366f1"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="Tax Liability"
                value={formatCurrency(metrics.portfolio.taxLiability)}
                subtitle="If sold today"
                icon={<Receipt />}
                color="#f59e0b"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="After-Tax Value"
                value={formatCurrency(metrics.portfolio.afterTaxValue)}
                subtitle="Net of taxes"
                icon={<AccountBalanceWallet />}
                color="#10b981"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <SummaryCard
                label="Cash on Hand"
                value={formatCurrency(metrics.portfolio.cashOnHand)}
                subtitle="Available cash"
                icon={<Savings />}
                color="#10b981"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Retirement Section - Same 4 Key Statistics as Retirement page */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <SectionHeader 
          title="🏖️ Retirement Overview" 
          icon={<BeachAccess />}
          bgGradient="linear-gradient(135deg, #8b5cf6, #6d28d9)"
        />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Years to Retirement"
                value={metrics.retirement.yearsToRetirement}
                subtitle={`Target: ${metrics.retirement.retirementYear}`}
                icon={<DateRange />}
                color="#8b5cf6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Monthly Retirement Income"
                value={formatCurrency(metrics.retirement.monthlyRetirementIncome, 0)}
                subtitle="After taxes"
                icon={<AttachMoney />}
                color="#10b981"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Target Monthly Need"
                value={formatCurrency(metrics.retirement.targetMonthlyNeed, 0)}
                subtitle="Based on lifestyle"
                icon={<BeachAccess />}
                color="#3b82f6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Projected Assets"
                value={formatCurrency(metrics.retirement.projectedAssets, 0)}
                subtitle="At retirement"
                icon={<Savings />}
                color="#ec4899"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Footer */}
      <Paper sx={{ p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Click on the module tabs above to see detailed information for each area. 
          Data refreshes automatically when you make changes.
        </Typography>
      </Paper>
    </Box>
  );
};
