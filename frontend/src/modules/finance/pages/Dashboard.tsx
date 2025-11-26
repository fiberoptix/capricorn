/**
 * Finance Dashboard - Standardized UI/UX
 * Track income, expenses, and savings with time period analysis
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Paper,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Receipt,
  AttachMoney,
  CloudDone,
} from '@mui/icons-material';
import { financeAPI } from '../services/api';
import TimePeriodSelector from '../components/TimePeriodSelector';
import CumulativeSpendingChart from '../components/CumulativeSpendingChart';

interface DashboardData {
  summary: {
    total_income: number;
    total_expenses: number;
    balance: number;
    savings_rate: number;
    period: string;
    period_type: string;
    date_range: {
      start: string | null;
      end: string | null;
    };
  };
  recent_transactions: Array<{
    id: string;
    description: string;
    amount: number;
    date: string;
    type: string;
  }>;
  spending_by_category: Array<{
    category: string;
    amount: number;
  }>;
  quick_stats: {
    accounts: number;
    transactions_this_period: number;
    average_daily_spending: number;
    average_monthly_spending: number;
    months_of_data: number;
    data_start_date: string | null;
    data_end_date: string | null;
  };
}

interface ChartData {
  chart_data: Array<{
    date: string;
    categories: { [key: string]: number };
    cumulative: { [key: string]: number };
  }>;
  categories: string[];
  period: string;
  date_range: {
    start: string | null;
    end: string | null;
  };
}

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  trend?: {
    direction: 'up' | 'down';
    absoluteChange: number;
    prefix?: string;
    suffix?: string;
  };
}

const SummaryCard: React.FC<SummaryCardProps> = ({ 
  label, 
  value, 
  subtitle, 
  icon, 
  color = '#059669',
  trend 
}) => (
  <Card sx={{ height: '100%' }}>
    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
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
          {trend && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
              {trend.direction === 'up' ? (
                <TrendingUp sx={{ fontSize: 14, color: '#10b981' }} />
              ) : (
                <TrendingDown sx={{ fontSize: 14, color: '#ef4444' }} />
              )}
              <Typography variant="caption" color="text.secondary">
                {trend.direction === 'up' ? 'UP' : 'DOWN'} {trend.prefix || '$'}
                {Math.abs(trend.absoluteChange).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                {trend.suffix || ''} vs last period
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [lastPeriodData, setLastPeriodData] = useState<DashboardData | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentPeriod, setCurrentPeriod] = useState('this_year');

  // Calculate previous period for comparison
  const calculatePreviousPeriod = (period: string, startDate?: string, endDate?: string) => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();

    switch (period) {
      case 'this_month':
        const lastMonth = new Date(currentYear, currentMonth - 1, 1);
        const endOfLastMonth = new Date(currentYear, currentMonth, 0);
        return {
          period: 'date_range',
          startDate: lastMonth.toISOString().split('T')[0],
          endDate: endOfLastMonth.toISOString().split('T')[0]
        };
      
      case 'last_month':
        const monthBeforeLastMonth = new Date(currentYear, currentMonth - 2, 1);
        const endOfMonthBeforeLastMonth = new Date(currentYear, currentMonth - 1, 0);
        return {
          period: 'date_range',
          startDate: monthBeforeLastMonth.toISOString().split('T')[0],
          endDate: endOfMonthBeforeLastMonth.toISOString().split('T')[0]
        };
      
      case 'last_3_months':
        const threeMonthsBeforeStart = new Date(currentYear, currentMonth - 5, 1);
        const threeMonthsBeforeEnd = new Date(currentYear, currentMonth - 2, 0);
        return {
          period: 'date_range',
          startDate: threeMonthsBeforeStart.toISOString().split('T')[0],
          endDate: threeMonthsBeforeEnd.toISOString().split('T')[0]
        };
      
      case 'this_year':
        const todayInPreviousYear = new Date(currentYear - 1, now.getMonth(), now.getDate());
        return {
          period: 'date_range',
          startDate: `${currentYear - 1}-01-01`,
          endDate: todayInPreviousYear.toISOString().split('T')[0]
        };
      
      case 'date_range':
        if (startDate && endDate) {
          const start = new Date(startDate);
          const end = new Date(endDate);
          const duration = end.getTime() - start.getTime();
          const prevEnd = new Date(start.getTime() - 24 * 60 * 60 * 1000);
          const prevStart = new Date(prevEnd.getTime() - duration);
          return {
            period: 'date_range',
            startDate: prevStart.toISOString().split('T')[0],
            endDate: prevEnd.toISOString().split('T')[0]
          };
        }
        return null;
      
      case 'all_time':
        return null;
      
      default:
        return null;
    }
  };

  // Calculate trend information
  const calculateTrend = (current: number, previous: number): { direction: 'up' | 'down'; percentage: number; absoluteChange: number } => {
    if (previous === 0) {
      return { direction: current > 0 ? 'up' : 'down', percentage: 0, absoluteChange: current };
    }
    
    const change = current - previous;
    const percentage = (change / Math.abs(previous)) * 100;
    
    return {
      direction: change > 0 ? 'up' : 'down',
      percentage: Math.abs(percentage),
      absoluteChange: change
    };
  };

  // Fetch data from backend
  const fetchData = async (period: string = 'this_year', startDate?: string, endDate?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await financeAPI.testConnection();
      setIsConnected(true);
      
      const previousPeriod = calculatePreviousPeriod(period, startDate, endDate);
      
      const promises = [
        financeAPI.getFinancialSummary({ period, startDate, endDate }),
        financeAPI.getCumulativeSpending({ period, startDate, endDate })
      ];
      
      if (previousPeriod) {
        promises.push(
          financeAPI.getFinancialSummary({
            period: previousPeriod.period,
            startDate: previousPeriod.startDate,
            endDate: previousPeriod.endDate
          })
        );
      }
      
      const responses = await Promise.all(promises);
      const [dashboardResponse, chartResponse, lastPeriodResponse] = responses;
      
      if (dashboardResponse.data && dashboardResponse.data.data) {
        setDashboardData(dashboardResponse.data.data);
      } else if (dashboardResponse.data) {
        setDashboardData(dashboardResponse.data);
      } else {
        throw new Error('Failed to fetch dashboard data');
      }
      
      if (chartResponse.data && chartResponse.data.data) {
        setChartData(chartResponse.data.data);
      } else if (chartResponse.data) {
        setChartData(chartResponse.data);
      } else {
        throw new Error('Failed to fetch chart data');
      }
      
      if (lastPeriodResponse && lastPeriodResponse.data.success) {
        setLastPeriodData(lastPeriodResponse.data.data);
      } else {
        setLastPeriodData(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      setIsConnected(false);
      console.error('API Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData(currentPeriod);
  }, []);

  const handlePeriodChange = (period: string, startDate?: string, endDate?: string) => {
    setCurrentPeriod(period);
    fetchData(period, startDate, endDate);
  };

  const summary = dashboardData ? {
    totalBalance: dashboardData.summary.balance,
    monthlyIncome: dashboardData.summary.total_income,
    monthlyExpenses: dashboardData.summary.total_expenses,
    savings: dashboardData.summary.balance,
    totalTransactions: dashboardData.quick_stats.transactions_this_period,
    savingsRate: dashboardData.summary.savings_rate,
    period: dashboardData.summary.period,
    averageDailySpending: dashboardData.quick_stats.average_daily_spending,
    accounts: dashboardData.quick_stats.accounts,
  } : {
    totalBalance: 0,
    monthlyIncome: 0,
    monthlyExpenses: 0,
    savings: 0,
    totalTransactions: 0,
    savingsRate: 0,
    period: 'All Time',
    averageDailySpending: 0,
    accounts: 0,
  };

  const formatCurrency = (value: number) => {
    return `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  // Calculate monthly average - use backend's calculated values
  const calculateMonthlyAvg = () => {
    const quickStats = dashboardData?.quick_stats;
    
    // First priority: Use backend's average_monthly_spending (calculated from actual transaction dates)
    if (quickStats?.average_monthly_spending && quickStats.average_monthly_spending > 0) {
      const months = quickStats.months_of_data || 0;
      return {
        value: quickStats.average_monthly_spending,
        subtitle: months > 0 ? `Over ${months.toFixed(1)} months` : 'Based on transaction history'
      };
    }
    
    // Second priority: Use average daily spending * 30 (for shorter periods)
    if (quickStats?.average_daily_spending && quickStats.average_daily_spending > 0) {
      return {
        value: quickStats.average_daily_spending * 30,
        subtitle: 'Based on avg daily spend'
      };
    }
    
    return { value: 0, subtitle: 'No data available' };
  };

  const monthlyAvgData = calculateMonthlyAvg();

  // Format period name to human-readable string
  const formatPeriodName = (period: string, dateRange?: { start: string | null; end: string | null }) => {
    const now = new Date();
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December'];
    
    switch (period) {
      case 'this_month': {
        return `${months[now.getMonth()]} ${now.getFullYear()}`;
      }
      case 'last_month': {
        const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        return `${months[lastMonth.getMonth()]} ${lastMonth.getFullYear()}`;
      }
      case 'last_3_months': {
        const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 2, 1);
        const endMonth = new Date(now.getFullYear(), now.getMonth(), 0);
        return `${months[threeMonthsAgo.getMonth()].substring(0, 3)} - ${months[endMonth.getMonth()].substring(0, 3)} ${now.getFullYear()}`;
      }
      case 'this_year': {
        return `${now.getFullYear()}`;
      }
      case 'all_time': {
        return 'All Time';
      }
      case 'date_range': {
        if (dateRange?.start && dateRange?.end) {
          const startDate = new Date(dateRange.start);
          const endDate = new Date(dateRange.end);
          const startStr = `${months[startDate.getMonth()].substring(0, 3)} ${startDate.getDate()}, ${startDate.getFullYear()}`;
          const endStr = `${months[endDate.getMonth()].substring(0, 3)} ${endDate.getDate()}, ${endDate.getFullYear()}`;
          return `${startStr} - ${endStr}`;
        }
        return 'Custom Range';
      }
      default:
        // Handle raw API response formats
        if (period.includes('_')) {
          return period.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        }
        return period;
    }
  };

  // Loading Component
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error Component
  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">
          <Typography variant="h6" gutterBottom>Backend Connection Error</Typography>
          <Typography variant="body2">{error}</Typography>
          <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
            Make sure the backend server is running on port 5002
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #059669, #047857)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <AttachMoney sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Finance Manager
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Track the size and velocity of the wealth you're building
            </Typography>
            {isConnected && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5, opacity: 0.9 }}>
                <CloudDone sx={{ fontSize: 16 }} />
                <Typography variant="caption">Connected • Real-time data</Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Summary Cards - Dashboard Style */}
      <Paper sx={{ mb: 3, overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #059669, #047857)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5
        }}>
          <AccountBalance />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            💰 Period Summary: {formatPeriodName(currentPeriod, dashboardData?.summary.date_range)}
          </Typography>
        </Box>
        <CardContent sx={{ p: 2 }}>
          <Grid container spacing={2}>
            {/* Income Card */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ 
                      p: 1.5, 
                      borderRadius: 1.5, 
                      bgcolor: '#10b98115',
                      color: '#10b981',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <TrendingUp />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatPeriodName(currentPeriod, dashboardData?.summary.date_range)} Income
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#10b981', lineHeight: 1.2 }}>
                        ${summary.monthlyIncome.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Expenses Card */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ 
                      p: 1.5, 
                      borderRadius: 1.5, 
                      bgcolor: '#ef444415',
                      color: '#ef4444',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Receipt />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatPeriodName(currentPeriod, dashboardData?.summary.date_range)} Expenses
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#ef4444', lineHeight: 1.2 }}>
                        ${Math.abs(summary.monthlyExpenses).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Monthly Average Card */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ 
                      p: 1.5, 
                      borderRadius: 1.5, 
                      bgcolor: '#f59e0b15',
                      color: '#f59e0b',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <TrendingDown />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatPeriodName(currentPeriod, dashboardData?.summary.date_range)} Monthly Avg
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#f59e0b', lineHeight: 1.2 }}>
                        ${monthlyAvgData.value.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                        {monthlyAvgData.subtitle}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Savings Card */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ 
                      p: 1.5, 
                      borderRadius: 1.5, 
                      bgcolor: '#0ea5e915',
                      color: '#0ea5e9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <AccountBalance />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatPeriodName(currentPeriod, dashboardData?.summary.date_range)} Savings
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#0ea5e9', lineHeight: 1.2 }}>
                        ${summary.savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Savings Rate Card */}
            <Grid item xs={12} sm={6} md={2.4}>
              <Card sx={{ height: '100%' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ 
                      p: 1.5, 
                      borderRadius: 1.5, 
                      bgcolor: '#3b82f615',
                      color: '#3b82f6',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <TrendingUp />
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Savings Rate
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#3b82f6', lineHeight: 1.2 }}>
                        {summary.savingsRate.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                        Of After-Tax income
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Time Period Selector */}
      <Paper sx={{ mb: 3, p: 2, borderRadius: 2 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'text.secondary' }}>
          📅 Select Time Period
        </Typography>
        <TimePeriodSelector 
          onPeriodChange={handlePeriodChange} 
          currentPeriod={currentPeriod}
        />
      </Paper>

      {/* Cumulative Spending Chart */}
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
          <Receipt />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📊 Cumulative Spending Analysis
          </Typography>
        </Box>
        <CardContent>
          <CumulativeSpendingChart 
            data={chartData?.chart_data || []} 
            categories={chartData?.categories || []} 
            summary={dashboardData?.summary || { total_income: 0, total_expenses: 0, balance: 0 }}
          />
        </CardContent>
      </Paper>

      {/* Footer */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Use the time period selector to compare different periods.
          Trend arrows show how you're doing compared to the previous equivalent period.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Dashboard;
