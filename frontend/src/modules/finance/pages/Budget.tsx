/**
 * Budget Page - Standardized UI/UX
 * Year-over-year spending analysis by category
 */

import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  useTheme,
  CardContent,
  Grid,
} from '@mui/material';
import {
  DataGrid,
  GridToolbarContainer,
  GridToolbarColumnsButton,
  GridToolbarFilterButton,
  GridToolbarExport,
  GridToolbarQuickFilter,
} from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import {
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart,
  Receipt,
  DateRange,
} from '@mui/icons-material';
import { financeAPI } from '../services/api';

interface BudgetAnalysisData {
  category: string;
  thisYearTotal: number;
  thisYearMonthlyAvg: number;
  lastYearTotal: number;
  lastYearMonthlyAvg: number;
  avgMonthlyChange: number;
}

interface BudgetMetadata {
  current_year: number;
  previous_year: number;
  current_year_months: number;
  latest_transaction_date: string | null;
  total_categories: number;
}

const Budget: React.FC = () => {
  const theme = useTheme();
  const [budgetData, setBudgetData] = useState<BudgetAnalysisData[]>([]);
  const [metadata, setMetadata] = useState<BudgetMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const currentYear = new Date().getFullYear();
  const previousYear = currentYear - 1;

  const fetchBudgetData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      await financeAPI.testConnection();
      setIsConnected(true);
      
      const response = await financeAPI.getBudgetAnalysis();
      if (response.data && response.data.success && response.data.data) {
        setBudgetData(response.data.data);
        if (response.data.metadata) {
          setMetadata(response.data.metadata);
        }
      } else {
        throw new Error(response.data?.message || 'Failed to fetch budget data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchBudgetData(); }, []);

  const CustomToolbar = () => (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <GridToolbarExport />
      <Box sx={{ flexGrow: 1 }} />
      <GridToolbarQuickFilter />
    </GridToolbarContainer>
  );

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">
          <Typography variant="h6" gutterBottom>Budget Analysis Error</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  const dataGridRows = budgetData.map((item, index) => ({
    id: index,
    category: item.category,
    thisYearTotal: item.thisYearTotal,
    thisYearMonthlyAvg: item.thisYearMonthlyAvg,
    lastYearTotal: item.lastYearTotal,
    lastYearMonthlyAvg: item.lastYearMonthlyAvg,
    avgMonthlyChange: item.avgMonthlyChange,
  }));

  // Calculate summary totals
  const totals = budgetData.reduce((acc, item) => ({
    thisYearMonthlyAvg: acc.thisYearMonthlyAvg + Math.abs(item.thisYearMonthlyAvg || 0),
    thisYearTotal: acc.thisYearTotal + Math.abs(item.thisYearTotal || 0),
    lastYearTotal: acc.lastYearTotal + Math.abs(item.lastYearTotal || 0),
    lastYearMonthlyAvg: acc.lastYearMonthlyAvg + Math.abs(item.lastYearMonthlyAvg || 0),
  }), { thisYearMonthlyAvg: 0, thisYearTotal: 0, lastYearTotal: 0, lastYearMonthlyAvg: 0 });

  const monthlyChange = totals.thisYearMonthlyAvg - totals.lastYearMonthlyAvg;

  const columns: GridColDef[] = [
    {
      field: 'category',
      headerName: 'Category',
      width: 200,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>{params.value}</Typography>
      ),
    },
    {
      field: 'thisYearTotal',
      headerName: `${currentYear} (YTD) Total`,
      width: 160,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          ${params.value != null ? Math.abs(params.value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : 0}
        </Typography>
      ),
    },
    {
      field: 'thisYearMonthlyAvg',
      headerName: `${currentYear} Monthly Avg`,
      width: 180,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          ${params.value != null ? Math.abs(params.value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : 0}
        </Typography>
      ),
    },
    {
      field: 'lastYearTotal',
      headerName: `${previousYear} Total`,
      width: 160,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
          ${params.value != null ? Math.abs(params.value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : 0}
        </Typography>
      ),
    },
    {
      field: 'lastYearMonthlyAvg',
      headerName: `${previousYear} Monthly Avg`,
      width: 180,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
          ${params.value != null ? Math.abs(params.value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : 0}
        </Typography>
      ),
    },
    {
      field: 'avgMonthlyChange',
      headerName: 'Monthly Change',
      width: 180,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
          {params.value > 0 ? (
            <TrendingUp sx={{ fontSize: 16, color: theme.palette.error.main }} />
          ) : params.value < 0 ? (
            <TrendingDown sx={{ fontSize: 16, color: theme.palette.success.main }} />
          ) : null}
          <Typography variant="body2" sx={{ 
            fontWeight: 600,
            color: params.value > 0 ? theme.palette.error.main : params.value < 0 ? theme.palette.success.main : 'text.primary',
          }}>
            {params.value > 0 ? '+' : ''}${params.value != null ? params.value.toLocaleString('en-US', { maximumFractionDigits: 0 }) : 0}
          </Typography>
        </Box>
      ),
    },
  ];

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #f59e0b, #d97706)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <PieChart sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Budget Analysis
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Year-over-year spending analysis by category ({currentYear} vs {previousYear})
            </Typography>
            {isConnected && (
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                📊 Connected • Analyzing {budgetData.length} categories
              </Typography>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Summary Cards - Dashboard Style */}
      <Paper sx={{ overflow: 'hidden', borderRadius: 2, mb: 3 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #059669, #047857)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5
        }}>
          <BarChart />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📈 Spending Summary
          </Typography>
        </Box>
        <CardContent sx={{ p: 2 }}>
          <Grid container spacing={2}>
            {/* Average Monthly Spending - This Year */}
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ 
                bgcolor: 'white',
                borderRadius: 2,
                p: 2,
                height: '100%',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 1.5
              }}>
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
                    Avg Monthly ({currentYear})
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#10b981', lineHeight: 1.2 }}>
                    ${totals.thisYearMonthlyAvg.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                    {metadata?.current_year_months ? `Based on ${metadata.current_year_months} months` : 'Year to date'}
                  </Typography>
                  {monthlyChange !== 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                      {monthlyChange < 0 ? (
                        <TrendingDown sx={{ fontSize: 14, color: theme.palette.success.main }} />
                      ) : (
                        <TrendingUp sx={{ fontSize: 14, color: theme.palette.error.main }} />
                      )}
                      <Typography variant="caption" sx={{ 
                        color: monthlyChange < 0 ? theme.palette.success.main : theme.palette.error.main,
                        fontWeight: 'bold'
                      }}>
                        ${Math.abs(monthlyChange).toLocaleString('en-US', { maximumFractionDigits: 0 })} vs last year
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            </Grid>

            {/* This Year Total (YTD) */}
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ 
                bgcolor: 'white',
                borderRadius: 2,
                p: 2,
                height: '100%',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 1.5
              }}>
                <Box sx={{ 
                  p: 1.5, 
                  borderRadius: 1.5, 
                  bgcolor: '#3b82f615',
                  color: '#3b82f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Receipt />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {currentYear} Total (YTD)
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#3b82f6', lineHeight: 1.2 }}>
                    ${totals.thisYearTotal.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                    Year to date spending
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {/* Last Year Total */}
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ 
                bgcolor: 'white',
                borderRadius: 2,
                p: 2,
                height: '100%',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 1.5
              }}>
                <Box sx={{ 
                  p: 1.5, 
                  borderRadius: 1.5, 
                  bgcolor: '#6b728015',
                  color: '#6b7280',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <DateRange />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {previousYear} Total
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#6b7280', lineHeight: 1.2 }}>
                    ${totals.lastYearTotal.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                    Full year comparison
                  </Typography>
                </Box>
              </Box>
            </Grid>

            {/* Last Year Monthly Avg */}
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ 
                bgcolor: 'white',
                borderRadius: 2,
                p: 2,
                height: '100%',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 1.5
              }}>
                <Box sx={{ 
                  p: 1.5, 
                  borderRadius: 1.5, 
                  bgcolor: '#9ca3af15',
                  color: '#9ca3af',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <PieChart />
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    Avg Monthly ({previousYear})
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 'bold', color: '#9ca3af', lineHeight: 1.2 }}>
                    ${totals.lastYearMonthlyAvg.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                    Baseline comparison
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Paper>

      {/* Budget Analysis DataGrid */}
      <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <BarChart />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📊 Category Comparison
          </Typography>
        </Box>
        <CardContent>
          <DataGrid
            rows={dataGridRows}
            columns={columns}
            initialState={{
              sorting: { sortModel: [{ field: 'thisYearTotal', sort: 'desc' }] },
              pagination: { paginationModel: { pageSize: Math.min(budgetData.length, 100) } },
            }}
            pagination
            paginationMode="client"
            pageSizeOptions={[25, 50, 100]}
            hideFooter={budgetData.length <= 100}
            checkboxSelection
            disableRowSelectionOnClick
            density="compact"
            slots={{ toolbar: CustomToolbar }}
            slotProps={{ toolbar: { showQuickFilter: true, quickFilterProps: { debounceMs: 500 } } }}
            sx={{
              minHeight: 600,
              '& .MuiDataGrid-columnHeader': {
                backgroundColor: '#f59e0b',
                color: 'white',
                fontWeight: 600,
              },
            }}
          />
        </CardContent>
      </Paper>

      {/* Footer */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Green arrows (↓) indicate spending decreased compared to last year. Red arrows (↑) indicate increased spending.
          Use the search and filters to find specific categories.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Budget;
