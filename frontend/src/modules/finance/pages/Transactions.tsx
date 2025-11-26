/**
 * Transactions Page - Standardized UI/UX
 * View and manage all financial transactions
 */

import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  Chip,
  useTheme,
  Tooltip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemAvatar,
  Avatar,
  Divider,
  IconButton,
} from '@mui/material';
import {
  DataGrid,
  GridToolbarContainer,
  GridToolbarColumnsButton,
  GridToolbarFilterButton,
  GridToolbarExport,
  GridToolbarQuickFilter,
  useGridApiContext,
} from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Receipt,
  DensitySmall,
  DensityMedium,
  ViewHeadline,
  Delete,
  Warning,
  List as ListIcon,
} from '@mui/icons-material';
import { financeAPI } from '../services/api';
import TimePeriodSelector from '../components/TimePeriodSelector';
import CategoryDropdown from '../components/CategoryDropdown';

interface Transaction {
  id: string;
  transaction_date: string;
  description: string;
  amount: number;
  transaction_type: string;
  account_id: string;
  account_name: string;
  category_id: string | null;
  category_name: string | null;
  spender: string | null;
}

interface TransactionSummary {
  total_transactions: number;
  total_income: number;
  total_expenses: number;
  balance: number;
  period: string;
  period_type: string;
  date_range: {
    start: string | null;
    end: string | null;
  };
}

interface DoubleChargeGroup {
  primary_transaction: {
    id: string;
    transaction_date: string;
    description: string;
    amount: number;
    transaction_type: string;
    created_at: string;
  };
  matching_transactions: Array<{
    id: string;
    transaction_date: string;
    description: string;
    amount: number;
    transaction_type: string;
    created_at: string;
    days_apart: number;
  }>;
  total_matches: number;
}

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, subtitle, icon, color = '#059669' }) => (
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

const CustomDensitySelector = () => {
  const apiRef = useGridApiContext();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handleDensityChange = (density: 'compact' | 'standard') => {
    apiRef.current.setDensity(density);
    handleClose();
  };
  
  return (
    <>
      <Button
        size="small"
        startIcon={<ViewHeadline />}
        onClick={handleClick}
        sx={{ minWidth: 'auto', color: 'text.secondary' }}
      >
        Density
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <MenuItem onClick={() => handleDensityChange('compact')}>
          <ListItemIcon><DensitySmall fontSize="small" /></ListItemIcon>
          <ListItemText>Compact</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDensityChange('standard')}>
          <ListItemIcon><DensityMedium fontSize="small" /></ListItemIcon>
          <ListItemText>Standard</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};

const CustomToolbar = () => (
  <GridToolbarContainer>
    <GridToolbarColumnsButton />
    <GridToolbarFilterButton />
    <CustomDensitySelector />
    <GridToolbarExport />
    <GridToolbarQuickFilter />
  </GridToolbarContainer>
);

const Transactions: React.FC = () => {
  const theme = useTheme();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentPeriod, setCurrentPeriod] = useState('this_year');
  const [showUntaggedOnly, setShowUntaggedOnly] = useState(false);
  const [categoryDropdown, setCategoryDropdown] = useState<{
    anchorEl: HTMLElement | null;
    transactionId: string | null;
    currentCategory: string | null;
  }>({ anchorEl: null, transactionId: null, currentCategory: null });

  const [showDoubleCharges, setShowDoubleCharges] = useState(false);
  const [doubleCharges, setDoubleCharges] = useState<DoubleChargeGroup[]>([]);
  const [doubleChargesDialog, setDoubleChargesDialog] = useState(false);
  const [isLoadingDoubleCharges, setIsLoadingDoubleCharges] = useState(false);

  const fetchData = async (period: string = 'this_year', startDate?: string, endDate?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      await financeAPI.testConnection();
      setIsConnected(true);
      
      const transactionsResponse = await financeAPI.getTransactions({
        period, startDate, endDate, limit: 5000
      });
      
      if (transactionsResponse.data) {
        const transData = transactionsResponse.data.data || transactionsResponse.data;
        setTransactions(transData.transactions || []);
        setSummary({
          total_transactions: transData.total_transactions || 0,
          total_income: transData.total_income || 0,
          total_expenses: transData.total_expenses || 0,
          balance: transData.balance || 0,
          period: transData.period || 'Unknown',
          period_type: transData.period_type || 'all_time',
          date_range: transData.date_range || { start: null, end: null }
        });
      } else {
        throw new Error('Failed to fetch data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to backend');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchData(currentPeriod); }, []);

  const handlePeriodChange = (period: string, startDate?: string, endDate?: string) => {
    setCurrentPeriod(period);
    setShowUntaggedOnly(false);
    fetchData(period, startDate, endDate);
  };

  const handleFixUntagged = () => {
    if (currentPeriod !== 'all_time') {
      setCurrentPeriod('all_time');
      fetchData('all_time');
    }
    setShowUntaggedOnly(!showUntaggedOnly);
  };

  const handleDoubleCharges = async () => {
    if (currentPeriod !== 'all_time') {
      setCurrentPeriod('all_time');
      fetchData('all_time');
    }
    setIsLoadingDoubleCharges(true);
    setShowDoubleCharges(true);
    try {
      const response = await financeAPI.getDoubleCharges();
      setDoubleCharges(response.data.data.double_charge_groups || []);
      setDoubleChargesDialog(true);
    } catch (error) {
      setDoubleCharges([]);
      setDoubleChargesDialog(true);
    } finally {
      setIsLoadingDoubleCharges(false);
    }
  };

  const handleDeleteTransaction = async (transactionId: string, description: string) => {
    if (window.confirm(`Are you sure you want to delete this transaction?\n\n"${description}"`)) {
      try {
        const response = await financeAPI.deleteTransaction(transactionId);
        if (response.data?.success) {
          setTransactions(prev => prev.filter(tx => tx.id !== transactionId));
          const doubleChargesResponse = await financeAPI.getDoubleCharges();
          if (doubleChargesResponse.data?.success) {
            setDoubleCharges(doubleChargesResponse.data.data.double_charge_groups || []);
          }
        }
      } catch (error) {
        alert('Failed to delete transaction. Please try again.');
      }
    }
  };

  const handleCategoryClick = (event: React.MouseEvent<HTMLElement>, transaction: Transaction) => {
    event.stopPropagation();
    setCategoryDropdown({
      anchorEl: event.currentTarget,
      transactionId: transaction.id,
      currentCategory: transaction.category_name,
    });
  };

  const handleCategoryDropdownClose = () => {
    setCategoryDropdown({ anchorEl: null, transactionId: null, currentCategory: null });
  };

  const handleCategorySelect = async (categoryId: string, categoryName: string) => {
    if (!categoryDropdown.transactionId) return;
    try {
      const response = await financeAPI.updateTransactionCategory(categoryDropdown.transactionId, categoryId);
      if (response.data?.success) {
        setTransactions(prev =>
          prev.map(tx =>
            tx.id === categoryDropdown.transactionId
              ? { ...tx, category_name: categoryName, category_id: categoryId }
              : tx
          )
        );
        handleCategoryDropdownClose();
      }
    } catch (error) {
      console.error('Error updating transaction category:', error);
    }
  };

  const filteredTransactions = showUntaggedOnly 
    ? transactions.filter(tx => !tx.category_name || tx.category_name === 'Uncategorized')
    : transactions;

  const dataGridRows = filteredTransactions.map((transaction, index) => ({
    id: transaction.id || index,
    date: transaction.transaction_date,
    description: transaction.description,
    amount: transaction.amount,
    category: transaction.category_name || 'Uncategorized',
    account: transaction.account_name || 'Unknown Account',
    spender: transaction.spender || 'Unknown',
    tag: transaction.transaction_type || (transaction.amount > 0 ? 'credit' : 'debit'),
    originalTransaction: transaction,
  }));

  const formatCurrency = (value: number) => {
    return `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

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
          <Typography variant="h6" gutterBottom>Backend Connection Error</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  const columns: GridColDef[] = [
    {
      field: 'date',
      headerName: 'Date',
      width: 120,
      valueFormatter: (value) => {
        if (!value) return '';
        if (typeof value === 'string') {
          const [year, month, day] = value.split('-');
          return `${month}/${day}/${year}`;
        }
        return value instanceof Date ? value.toLocaleDateString() : '';
      },
    },
    {
      field: 'description',
      headerName: 'Description',
      minWidth: 200,
      flex: 1,
      renderCell: (params) => (
        <Tooltip title={params.value} arrow>
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }}>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'amount',
      headerName: 'Amount',
      width: 140,
      type: 'number',
      align: 'right',
      headerAlign: 'left',
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
          {params.value > 0 ? (
            <TrendingUp sx={{ fontSize: 16, color: theme.palette.success.main }} />
          ) : (
            <TrendingDown sx={{ fontSize: 16, color: theme.palette.error.main }} />
          )}
          <Typography variant="body2" sx={{ fontWeight: 600, color: params.value > 0 ? theme.palette.success.main : theme.palette.error.main }}>
            ${Math.abs(params.value).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 180,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          onClick={(event) => handleCategoryClick(event, params.row.originalTransaction)}
          sx={{
            backgroundColor: params.value === 'Uncategorized' ? '#f57c00' : theme.palette.primary.main,
            color: 'white',
            fontWeight: 500,
            cursor: 'pointer',
            '&:hover': { transform: 'scale(1.05)' },
          }}
        />
      ),
    },
    {
      field: 'account',
      headerName: 'Account',
      width: 220,
      renderCell: (params) => (
        <Chip label={params.value} size="small" variant="outlined" sx={{ borderColor: theme.palette.secondary.main, color: theme.palette.secondary.main }} />
      ),
    },
    { field: 'spender', headerName: 'Spender' },
    {
      field: 'tag',
      headerName: 'Type',
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          sx={{
            backgroundColor: params.value === 'debit' ? '#ffebee' : '#e8f5e8',
            color: params.value === 'debit' ? '#c62828' : '#2e7d32',
            fontWeight: 500,
          }}
        />
      ),
    },
  ];

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
          <ListIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Transaction Management
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              View and search all your financial transactions
            </Typography>
            {isConnected && (
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                📊 Connected • Loaded {dataGridRows.length} of {summary?.total_transactions || 0} transactions
              </Typography>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Summary Cards */}
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
          <Receipt />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            💰 Period Summary: {summary?.period || 'All Time'}
          </Typography>
        </Box>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Period Income"
                value={formatCurrency(summary?.total_income || 0)}
                icon={<TrendingUp />}
                color={(summary?.total_income || 0) >= 0 ? '#10b981' : '#ef4444'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Period Expenses"
                value={formatCurrency(summary?.total_expenses || 0)}
                icon={<TrendingDown />}
                color={(summary?.total_expenses || 0) >= 0 ? '#ef4444' : '#10b981'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Period Savings"
                value={formatCurrency(summary?.balance || 0)}
                icon={<AccountBalance />}
                color={(summary?.balance || 0) >= 0 ? '#10b981' : '#ef4444'}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <SummaryCard
                label="Transactions"
                value={summary?.total_transactions || 0}
                icon={<Receipt />}
                color="#3b82f6"
              />
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
          onFixUntagged={handleFixUntagged}
          showFixUntagged={showUntaggedOnly}
          onDoubleCharges={handleDoubleCharges}
          showDoubleCharges={showDoubleCharges}
          isLoadingDoubleCharges={isLoadingDoubleCharges}
        />
      </Paper>

      {/* Transaction DataGrid */}
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
          <ListIcon />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📋 Transaction List
          </Typography>
        </Box>
        <Box sx={{ p: 2 }}>
          <DataGrid
            rows={dataGridRows}
            columns={columns}
            initialState={{
              sorting: { sortModel: [{ field: 'date', sort: 'desc' }] },
              density: 'compact',
              pagination: { paginationModel: { pageSize: 100 } },
            }}
            pagination
            paginationMode="client"
            pageSizeOptions={[25, 50, 100, 200, 500]}
            checkboxSelection
            disableRowSelectionOnClick
            slots={{ toolbar: CustomToolbar }}
            slotProps={{ toolbar: { showQuickFilter: true, quickFilterProps: { debounceMs: 500 } } }}
            sx={{
              minHeight: 500,
              '& .MuiDataGrid-columnHeader': {
                backgroundColor: '#059669',
                color: 'white',
                fontWeight: 600,
              },
            }}
          />
        </Box>
      </Paper>

      {/* Footer */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Click on a category chip to change the category. Use the toolbar to filter, sort, and export transactions.
        </Typography>
      </Paper>

      {/* Double Charges Dialog */}
      <Dialog open={doubleChargesDialog} onClose={() => setDoubleChargesDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <Warning color="error" />
            <Typography variant="h6">Potential Duplicate Debit Charges</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {doubleCharges.length === 0 ? (
            <Box display="flex" flexDirection="column" alignItems="center" p={4}>
              <Typography variant="h6" color="success.main" gutterBottom>✅ No Double Charges Found</Typography>
              <Typography variant="body2" color="text.secondary">All transactions appear to be unique.</Typography>
            </Box>
          ) : (
            <List>
              {doubleCharges.map((group, index) => (
                <Box key={index} sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                    Group {index + 1}: {group.primary_transaction.description}
                  </Typography>
                  <ListItem sx={{ bgcolor: 'primary.50', borderRadius: 1, mb: 1 }}>
                    <ListItemAvatar><Avatar sx={{ bgcolor: 'primary.main' }}><Receipt /></Avatar></ListItemAvatar>
                    <ListItemText primary={group.primary_transaction.description} secondary={`$${Math.abs(group.primary_transaction.amount).toFixed(2)}`} />
                    <IconButton onClick={() => handleDeleteTransaction(group.primary_transaction.id, group.primary_transaction.description)} color="error" size="small">
                      <Delete />
                    </IconButton>
                  </ListItem>
                  {group.matching_transactions.map((match, matchIndex) => (
                    <ListItem key={matchIndex} sx={{ bgcolor: 'error.50', borderRadius: 1, mb: 1 }}>
                      <ListItemAvatar><Avatar sx={{ bgcolor: 'error.main' }}><Warning /></Avatar></ListItemAvatar>
                      <ListItemText primary={match.description} secondary={`$${Math.abs(match.amount).toFixed(2)} • Same day duplicate`} />
                      <IconButton onClick={() => handleDeleteTransaction(match.id, match.description)} color="error" size="small">
                        <Delete />
                      </IconButton>
                    </ListItem>
                  ))}
                  {index < doubleCharges.length - 1 && <Divider sx={{ my: 2 }} />}
                </Box>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDoubleChargesDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <CategoryDropdown
        anchorEl={categoryDropdown.anchorEl}
        open={Boolean(categoryDropdown.anchorEl)}
        onClose={handleCategoryDropdownClose}
        onCategorySelect={handleCategorySelect}
        currentCategory={categoryDropdown.currentCategory || undefined}
        transactionId={categoryDropdown.transactionId || ''}
      />
    </Box>
  );
};

export default Transactions;
