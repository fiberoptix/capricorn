/**
 * Retirement Module
 * Displays retirement projections and analysis
 * All data comes from Profile tab (read-only display)
 */
import React, { useState } from 'react';
import { Box, Tabs, Tab, Typography, Grid, Paper } from '@mui/material';
import { RetirementDashboard } from './components/RetirementDashboard';
import { ProjectionsTable } from './components/ProjectionsTable';
import { AssetGrowthView } from './components/AssetGrowthView';
import { useRetirementSummary } from './hooks/use-retirement';
import { useProfile } from '../profile/hooks/use-profile';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
  fullWidth?: boolean;  // Allow full width for Annual Projections
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, fullWidth = false, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`retirement-tabpanel-${index}`}
      aria-labelledby={`retirement-tab-${index}`}
      {...other}
    >
      {value === index && (
        <div className={fullWidth ? "w-[95%] mx-auto" : ""}>
          {children}
        </div>
      )}
    </div>
  );
}

// Summary Card Component for standardized UI
interface SummaryCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, subtitle, icon, color = '#8b5cf6' }) => (
  <Paper sx={{ height: '100%' }}>
    <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
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
  </Paper>
);

// Combined Retirement Analysis + Transition Analysis
function RetirementAnalysisPanel() {
  const { data: summary, isLoading } = useRetirementSummary();
  const { data: profile } = useProfile();
  
  if (isLoading || !summary) return <Box p={3}>Loading...</Box>;
  
  const analysis = summary.retirement_analysis;
  const transition = summary.transition_analysis;
  const formatCurrency = (amount: number) => `$${Math.round(amount).toLocaleString()}`;
  
  // Get dynamic names
  const userName = profile?.user || 'User';
  const partnerName = profile?.partner || 'Partner';
  
  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ fontSize: 40 }}>🎯</Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Retirement Analysis
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Withdrawal strategy, lifestyle sustainability, and transition planning
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Summary Cards - Key Metrics */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #a78bfa, #8b5cf6)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Box sx={{ fontSize: 20 }}>💰</Box>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            Key Retirement Metrics
          </Typography>
        </Box>
        <Box sx={{ p: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Monthly Gross Withdrawal"
                value={formatCurrency(analysis.withdrawalAnalysis.monthlyGrossWithdrawal)}
                subtitle="Before taxes"
                icon={<Box>💵</Box>}
                color="#10b981"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Monthly Net Withdrawal"
                value={formatCurrency(analysis.withdrawalAnalysis.monthlyNetWithdrawal)}
                subtitle="After taxes"
                icon={<Box>💰</Box>}
                color="#3b82f6"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Monthly Tax"
                value={formatCurrency(analysis.withdrawalAnalysis.monthlyTax)}
                subtitle="Tax withheld"
                icon={<Box>📋</Box>}
                color="#ef4444"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Lifestyle Multiple"
                value={`${analysis.lifestyleAnalysis.lifestyleMultiple.toFixed(1)}x`}
                subtitle="Sustainability factor"
                icon={<Box>⭐</Box>}
                color="#f59e0b"
              />
            </Grid>
          </Grid>
        </Box>
      </Paper>
      
      {/* Withdrawal & Lifestyle Analysis */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ overflow: 'hidden', borderRadius: 2, height: '100%' }}>
            <Box sx={{ 
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: 'white',
              px: 2,
              py: 1.5,
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}>
              <Box sx={{ fontSize: 20 }}>📈</Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Withdrawal Strategy
              </Typography>
            </Box>
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, pb: 2, borderBottom: '1px solid #e5e7eb' }}>
                <Typography color="text.secondary">Monthly Gross</Typography>
                <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(analysis.withdrawalAnalysis.monthlyGrossWithdrawal)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, pb: 2, borderBottom: '1px solid #e5e7eb' }}>
                <Typography color="text.secondary">Monthly Tax</Typography>
                <Typography sx={{ fontWeight: 'bold', color: '#ef4444' }}>-{formatCurrency(analysis.withdrawalAnalysis.monthlyTax)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', bgcolor: '#f0fdf4', p: 2, borderRadius: 1 }}>
                <Typography sx={{ fontWeight: 'bold' }}>Monthly Net</Typography>
                <Typography sx={{ fontWeight: 'bold', color: '#10b981', fontSize: '1.25rem' }}>{formatCurrency(analysis.withdrawalAnalysis.monthlyNetWithdrawal)}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ overflow: 'hidden', borderRadius: 2, height: '100%' }}>
            <Box sx={{ 
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: 'white',
              px: 2,
              py: 1.5,
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}>
              <Box sx={{ fontSize: 20 }}>🏠</Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Lifestyle Sustainability
              </Typography>
            </Box>
            <Box sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, pb: 2, borderBottom: '1px solid #e5e7eb' }}>
                <Typography color="text.secondary">Target Monthly Need</Typography>
                <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(analysis.lifestyleAnalysis.targetMonthlyNeed)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, pb: 2, borderBottom: '1px solid #e5e7eb' }}>
                <Typography color="text.secondary">Monthly Surplus</Typography>
                <Typography sx={{ fontWeight: 'bold', color: analysis.lifestyleAnalysis.monthlySurplus >= 0 ? '#10b981' : '#ef4444' }}>
                  {analysis.lifestyleAnalysis.monthlySurplus >= 0 ? '+' : ''}{formatCurrency(analysis.lifestyleAnalysis.monthlySurplus)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', bgcolor: '#fffbeb', p: 2, borderRadius: 1 }}>
                <Typography sx={{ fontWeight: 'bold' }}>Lifestyle Multiple</Typography>
                <Typography sx={{ fontWeight: 'bold', color: '#f59e0b', fontSize: '1.25rem' }}>{analysis.lifestyleAnalysis.lifestyleMultiple.toFixed(1)}x</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Transition Period Analysis Card */}
      <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Box sx={{ fontSize: 20 }}>🔄</Box>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            Transition Period Analysis
          </Typography>
        </Box>
        <Box sx={{ p: 3 }}>
          {transition.transitionPeriod.duration === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary">{transition.transitionPeriod.message}</Typography>
            </Box>
          ) : (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, p: 2, bgcolor: '#eff6ff', borderRadius: 2 }}>
                <Box sx={{ p: 2, bgcolor: '#3b82f6', color: 'white', borderRadius: 1.5, fontWeight: 'bold', fontSize: '1.5rem' }}>
                  {transition.transitionPeriod.duration}
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Years of Transition
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {transition.transitionPeriod.startYear} - {transition.transitionPeriod.endYear} • {userName} retires, {partnerName} continues working
                  </Typography>
                </Box>
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: '#eff6ff', borderRadius: 2, border: '1px solid #bfdbfe' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#1d4ed8', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box>💼</Box> {partnerName}'s Income
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">Start Year ({transition.transitionPeriod.startYear})</Typography>
                      <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.incomeAnalysis.partnerSalaryStart)}</Typography>
                    </Box>
                    {transition.transitionPeriod.duration > 2 && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">Mid Period</Typography>
                        <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.incomeAnalysis.partnerSalaryMid)}</Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">End Year ({transition.transitionPeriod.endYear})</Typography>
                      <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.incomeAnalysis.partnerSalaryEnd)}</Typography>
                    </Box>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: '#fefce8', borderRadius: 2, border: '1px solid #fde68a' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: '#ca8a04', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box>📊</Box> Expense Coverage
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">Start Year</Typography>
                      <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.expenseCoverage.expensesStart)}</Typography>
                    </Box>
                    {transition.transitionPeriod.duration > 2 && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">Mid Period</Typography>
                        <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.expenseCoverage.expensesMid)}</Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">End Year</Typography>
                      <Typography sx={{ fontWeight: 'bold' }}>{formatCurrency(transition.expenseCoverage.expensesEnd)}</Typography>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Footer */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> The lifestyle multiple shows how many times your projected income covers your target expenses. 
          A multiple above 1.0x means you'll have surplus income in retirement.
        </Typography>
      </Paper>
    </Box>
  );
}

export function RetirementModule() {
  const [activeTab, setActiveTab] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleChange}
          aria-label="retirement tabs"
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              minWidth: 100,
            }
          }}
        >
          <Tab label="Overview" />
          <Tab label="Annual Projections" />
          <Tab label="Asset Growth" />
          <Tab label="Retirement Analysis" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <RetirementDashboard />
      </TabPanel>
      <TabPanel value={activeTab} index={1} fullWidth={true}>
        <ProjectionsTable />
      </TabPanel>
      <TabPanel value={activeTab} index={2} fullWidth={true}>
        <AssetGrowthView />
      </TabPanel>
      <TabPanel value={activeTab} index={3}>
        <RetirementAnalysisPanel />
      </TabPanel>
    </Box>
  );
}

export default RetirementModule;

