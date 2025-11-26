/**
 * Retirement Dashboard Component - Standardized UI/UX
 * Overview of retirement projections and status
 */
import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  CircularProgress, 
  Alert,
  Card,
  CardContent,
  Divider 
} from '@mui/material';
import { 
  TrendingUp, 
  AccountBalance, 
  BeachAccess,
  DateRange,
  AttachMoney,
  Savings,
  Assessment,
  CheckCircle,
  Warning,
  Schedule
} from '@mui/icons-material';
import { useRetirementSummary } from '../hooks/use-retirement';
import { useProfile } from '../../profile/hooks/use-profile';
import { AssetGrowthChart } from './AssetGrowthChart';

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ 
  label, 
  value, 
  subtitle, 
  icon, 
  color = '#8b5cf6' 
}) => (
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
          <Typography variant="h5" sx={{ fontWeight: 'bold', color, lineHeight: 1.2 }}>
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

// Asset Item Component
interface AssetItemProps {
  label: string;
  value: string;
  color?: string;
  isBold?: boolean;
}

const AssetItem: React.FC<AssetItemProps> = ({ label, value, color = 'text.primary', isBold = false }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
    <Typography variant="body2" color="text.secondary">
      {label}
    </Typography>
    <Typography 
      variant={isBold ? 'h6' : 'body1'} 
      sx={{ fontWeight: isBold ? 'bold' : 'medium', color }}
    >
      {value}
    </Typography>
  </Box>
);

export function RetirementDashboard() {
  const { data: summary, isLoading, error } = useRetirementSummary();
  const { data: profile } = useProfile();

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load retirement data: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!summary) {
    return <Alert severity="info">No retirement data available</Alert>;
  }

  const { retirement_analysis, summary: summaryData } = summary;
  const currentYear = 2025;
  const yearsToRetirement = summaryData.user_retirement_year - currentYear;
  
  const userName = profile?.user || 'User';
  const partnerName = profile?.partner || 'Partner';

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const { asset_growth } = summary;

  // Status color helper
  const getStatusColor = (status: string) => {
    if (status.toLowerCase().includes('on track') || status.toLowerCase().includes('healthy')) return '#10b981';
    if (status.toLowerCase().includes('caution') || status.toLowerCase().includes('watch')) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <BeachAccess sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Retirement Planner
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Your path to financial freedom starts here
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Key Statistics */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #a855f7, #8b5cf6)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Assessment />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📊 Key Statistics
          </Typography>
        </Box>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Years to Retirement"
                value={yearsToRetirement}
                subtitle={`Target: ${summaryData.user_retirement_year}`}
                icon={<Schedule />}
                color="#8b5cf6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Monthly Retirement Income"
                value={formatCurrency(retirement_analysis.withdrawalAnalysis.monthlyNetWithdrawal)}
                subtitle="After taxes"
                icon={<AttachMoney />}
                color="#10b981"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Target Monthly Need"
                value={formatCurrency(retirement_analysis.lifestyleAnalysis.targetMonthlyNeed)}
                subtitle="Based on lifestyle"
                icon={<DateRange />}
                color="#3b82f6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Projected Assets"
                value={formatCurrency(summaryData.final_assets)}
                subtitle="At retirement"
                icon={<Savings />}
                color="#ec4899"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Projected Assets Breakdown */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #10b981, #059669)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <AccountBalance />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            💰 Projected Retirement Assets ({summaryData.user_retirement_year})
          </Typography>
        </Box>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
                  Retirement Accounts
                </Typography>
                <AssetItem label={`${userName} 401K`} value={formatCurrency(retirement_analysis.finalAssetValues.userAccount401k)} />
                <AssetItem label={`${partnerName} 401K`} value={formatCurrency(retirement_analysis.finalAssetValues.partnerAccount401k)} />
                <AssetItem label="IRA Balance" value={formatCurrency(retirement_analysis.finalAssetValues.accountIRA)} />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'secondary.main' }}>
                  Other Assets
                </Typography>
                <AssetItem label="Trading Account" value={formatCurrency(retirement_analysis.finalAssetValues.accountTrading)} />
                <AssetItem label="Inheritance" value={formatCurrency(retirement_analysis.finalAssetValues.inheritance)} />
                <Divider sx={{ my: 1 }} />
                <AssetItem 
                  label="TOTAL ASSETS" 
                  value={formatCurrency(retirement_analysis.finalAssetValues.totalAssets)} 
                  color="#10b981"
                  isBold
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Retirement Outlook */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <TrendingUp />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            🎯 Retirement Outlook
          </Typography>
        </Box>
        <CardContent>
          <Grid container spacing={3}>
            {/* Withdrawal Analysis */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', bgcolor: 'blue.50', border: '1px solid', borderColor: 'blue.200' }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#3b82f6', mb: 2 }}>
                    💵 Withdrawal Analysis
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Monthly Gross</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatCurrency(retirement_analysis.withdrawalAnalysis.monthlyGrossWithdrawal)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Monthly Tax</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#ef4444' }}>
                        -{formatCurrency(retirement_analysis.withdrawalAnalysis.monthlyTax)}
                      </Typography>
                    </Box>
                    <Divider />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Monthly Net</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#10b981' }}>
                        {formatCurrency(retirement_analysis.withdrawalAnalysis.monthlyNetWithdrawal)}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Lifestyle Analysis */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', bgcolor: 'purple.50', border: '1px solid', borderColor: 'purple.200' }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#8b5cf6', mb: 2 }}>
                    🏠 Lifestyle Analysis
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Target Need</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {formatCurrency(retirement_analysis.lifestyleAnalysis.targetMonthlyNeed)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">Monthly Surplus</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', color: retirement_analysis.lifestyleAnalysis.monthlySurplus >= 0 ? '#10b981' : '#ef4444' }}>
                        {formatCurrency(retirement_analysis.lifestyleAnalysis.monthlySurplus)}
                      </Typography>
                    </Box>
                    <Divider />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>Lifestyle Multiple</Typography>
                      <Typography variant="body1" sx={{ fontWeight: 'bold', color: '#8b5cf6' }}>
                        {retirement_analysis.lifestyleAnalysis.lifestyleMultiple.toFixed(1)}x
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Status Indicators */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%', bgcolor: 'green.50', border: '1px solid', borderColor: 'green.200' }}>
                <CardContent>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#10b981', mb: 2 }}>
                    ✅ Status Indicators
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Retirement Goal</Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 'bold', 
                          color: getStatusColor(retirement_analysis.statusIndicators.retirementGoal),
                          bgcolor: `${getStatusColor(retirement_analysis.statusIndicators.retirementGoal)}15`,
                          px: 1,
                          py: 0.25,
                          borderRadius: 1
                        }}
                      >
                        {retirement_analysis.statusIndicators.retirementGoal}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Savings Target</Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 'bold', 
                          color: getStatusColor(retirement_analysis.statusIndicators.savingsTarget),
                          bgcolor: `${getStatusColor(retirement_analysis.statusIndicators.savingsTarget)}15`,
                          px: 1,
                          py: 0.25,
                          borderRadius: 1
                        }}
                      >
                        {retirement_analysis.statusIndicators.savingsTarget}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Asset Growth</Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 'bold', 
                          color: getStatusColor(retirement_analysis.statusIndicators.assetGrowth),
                          bgcolor: `${getStatusColor(retirement_analysis.statusIndicators.assetGrowth)}15`,
                          px: 1,
                          py: 0.25,
                          borderRadius: 1
                        }}
                      >
                        {retirement_analysis.statusIndicators.assetGrowth}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Asset Growth Chart */}
      {asset_growth && asset_growth.length > 0 && (
        <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
          <Box sx={{ 
            background: 'linear-gradient(135deg, #f59e0b, #d97706)',
            color: 'white',
            px: 2,
            py: 1.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            <TrendingUp />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              📈 Asset Growth Projection
            </Typography>
          </Box>
          <CardContent>
            <AssetGrowthChart data={asset_growth} userName={userName} partnerName={partnerName} />
          </CardContent>
        </Paper>
      )}

      {/* Footer */}
      <Paper sx={{ p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Update your profile settings to see how changes in retirement age, savings rate, 
          or expected returns affect your retirement projections.
        </Typography>
      </Paper>
    </Box>
  );
}
