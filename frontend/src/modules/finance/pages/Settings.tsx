/**
 * Settings Page - Standardized UI/UX
 * Finance data summary and category management
 * 
 * Note: Export/Import/Clear functionality moved to DATA tab (Phase 10)
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Stack,
} from '@mui/material';
import {
  Storage,
  Description,
  Category,
  AccountBalance,
  CalendarToday,
  Schedule,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { financeAPI } from '../services/api';
import TagsSummary from '../components/TagsSummary';

interface DataSummary {
  transactions: number;
  accounts: number;
  categories: number;
  files: number;
  file_details?: { [key: string]: number };
}

interface AccountRange {
  account_name: string;
  earliest_date: string;
  latest_date: string;
  transaction_count: number;
}

interface TransactionDateRanges {
  account_ranges: AccountRange[];
}

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, icon, color = '#3b82f6' }) => (
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
          <Typography variant="h6" sx={{ fontWeight: 'bold', color }}>
            {value}
          </Typography>
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const Settings: React.FC = () => {
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
  const [dateRanges, setDateRanges] = useState<TransactionDateRanges | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDataSummary();
    fetchTransactionDateRanges();
  }, []);

  const fetchDataSummary = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await financeAPI.getDataSummary();
      if (response.data.success) setDataSummary(response.data.data);
    } catch (err: any) {
      setError('Failed to fetch data summary');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchTransactionDateRanges = async () => {
    try {
      const response = await financeAPI.getTransactionDateRanges();
      if (response.data.success) setDateRanges(response.data.data);
    } catch (err: any) {
      setError('Failed to fetch transaction date ranges');
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #6b7280, #4b5563)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SettingsIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Finance Settings
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              View your finance data summary and manage categories
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Data Summary Section */}
      <Paper sx={{ overflow: 'hidden', borderRadius: 2, mb: 3 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Storage />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📊 Finance Data Summary
          </Typography>
        </Box>
        <CardContent>
          {isLoading ? (
            <Box display="flex" justifyContent="center" p={4}><CircularProgress /></Box>
          ) : dataSummary ? (
            <>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <SummaryCard icon={<Description />} label="Transactions" value={dataSummary.transactions.toLocaleString()} color="#3b82f6" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <SummaryCard icon={<AccountBalance />} label="Accounts" value={dataSummary.accounts} color="#10b981" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <SummaryCard icon={<Category />} label="Categories" value={dataSummary.categories} color="#f59e0b" />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <SummaryCard icon={<Storage />} label="Files" value={dataSummary.files} color="#8b5cf6" />
                </Grid>
              </Grid>
              
              {dateRanges && dateRanges.account_ranges.length > 0 && (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Box display="flex" alignItems="center" gap={2} mb={2}>
                          <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: '#3b82f615', color: '#3b82f6' }}>
                            <CalendarToday />
                          </Box>
                          <Typography variant="h6" fontWeight="bold">Earliest Transaction</Typography>
                        </Box>
                        <Stack spacing={1}>
                          {dateRanges.account_ranges.map((range) => (
                            <Box key={range.account_name} display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">{range.account_name}:</Typography>
                              <Typography variant="body2" fontWeight="medium">{range.earliest_date}</Typography>
                            </Box>
                          ))}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Box display="flex" alignItems="center" gap={2} mb={2}>
                          <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: '#10b98115', color: '#10b981' }}>
                            <Schedule />
                          </Box>
                          <Typography variant="h6" fontWeight="bold">Latest Transaction</Typography>
                        </Box>
                        <Stack spacing={1}>
                          {dateRanges.account_ranges.map((range) => (
                            <Box key={range.account_name} display="flex" justifyContent="space-between">
                              <Typography variant="body2" color="text.secondary">{range.account_name}:</Typography>
                              <Typography variant="body2" fontWeight="medium">{range.latest_date}</Typography>
                            </Box>
                          ))}
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </>
          ) : (
            <Typography color="text.secondary">No data available</Typography>
          )}
        </CardContent>
      </Paper>

      {/* Category Management Section */}
      <TagsSummary />

      {/* Footer */}
      <Paper sx={{ mt: 3, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Use the <strong>Data</strong> tab at the top to export, import, or clear all your Capricorn data (Finance, Portfolio, Retirement, and Profile).
        </Typography>
      </Paper>
    </Box>
  );
};

export default Settings;
