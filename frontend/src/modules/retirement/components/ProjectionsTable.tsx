/**
 * Annual Projections Table
 * Displays 30-year financial projections
 */
import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Grid,
} from '@mui/material';
import { useRetirementSummary } from '../hooks/use-retirement';
import { useProfile } from '../../profile/hooks/use-profile';

export function ProjectionsTable() {
  const { data: summary, isLoading, error } = useRetirementSummary();
  const { data: profile } = useProfile();
  
  // Get dynamic names
  const userName = profile?.user || 'User';
  const partnerName = profile?.partner || 'Partner';

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
        Failed to load projections: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!summary || !summary.yearly_projections) {
    return <Alert severity="info">No projection data available</Alert>;
  }

  const formatCurrency = (amount: number) => `$${Math.round(amount).toLocaleString()}`;
  const formatPercent = (rate: number) => `${(rate * 100).toFixed(1)}%`;

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" gutterBottom sx={{ px: 2 }}>
        📈 Annual Financial Projections
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, px: 2 }}>
        30-year projection of income, expenses, taxes, and savings
      </Typography>

      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block', px: 2 }}>
        Maximize your browser window or scroll horizontally to view all table columns
      </Typography>

      <TableContainer component={Paper} sx={{ maxHeight: 700, overflow: 'auto', width: '100%' }}>
        <Table stickyHeader size="small" sx={{ width: '100%', tableLayout: 'auto' }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ position: 'sticky', left: 0, bgcolor: 'background.paper', zIndex: 3 }}><strong>Year</strong></TableCell>
              <TableCell align="right"><strong>{userName} Salary</strong></TableCell>
              <TableCell align="right"><strong>{userName} Bonus</strong></TableCell>
              <TableCell align="right"><strong>{partnerName} Salary</strong></TableCell>
              <TableCell align="right"><strong>{partnerName} Bonus</strong></TableCell>
              <TableCell align="right"><strong>Gross Income</strong></TableCell>
              <TableCell align="right"><strong>Taxable Income</strong></TableCell>
              <TableCell align="right"><strong>Total Taxes</strong></TableCell>
              <TableCell align="right"><strong>Take Home Pay</strong></TableCell>
              <TableCell align="right"><strong>Essential Expenses</strong></TableCell>
              <TableCell align="right"><strong>Discretionary Expenses</strong></TableCell>
              <TableCell align="right"><strong>Total Expenses</strong></TableCell>
              <TableCell align="right"><strong>Leftover Money</strong></TableCell>
              <TableCell align="right"><strong>Monthly Leftover</strong></TableCell>
              <TableCell align="right"><strong>Monthly Savings</strong></TableCell>
              <TableCell align="right"><strong>Annual Savings</strong></TableCell>
              <TableCell align="right"><strong>Total Withdrawals</strong></TableCell>
              <TableCell align="right"><strong>{userName} 401K</strong></TableCell>
              <TableCell align="right"><strong>{partnerName} 401K</strong></TableCell>
              <TableCell align="right"><strong>IRA Value</strong></TableCell>
              <TableCell align="right"><strong>Trading Value</strong></TableCell>
              <TableCell align="right"><strong>Inheritance</strong></TableCell>
              <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>Total Assets</strong></TableCell>
              <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>Net Worth</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {summary.yearly_projections.map((projection: any) => (
              <TableRow key={projection.year} hover>
                <TableCell sx={{ position: 'sticky', left: 0, bgcolor: 'background.paper', zIndex: 1 }}>{projection.year}</TableCell>
                <TableCell align="right">{formatCurrency(projection.user_salary)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.user_bonus)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.partner_salary)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.partner_bonus)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.gross_income)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.taxable_income)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.total_taxes)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.take_home_pay)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.essential_expenses)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.discretionary_expenses)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.total_expenses)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.leftover_money)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.monthly_leftover)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.monthly_savings)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.annual_savings)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.total_withdrawals)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.userAccount401k || 0)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.partnerAccount401k || 0)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.accountIRA || 0)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.accountTrading || 0)}</TableCell>
                <TableCell align="right">{formatCurrency(projection.inheritance || 0)}</TableCell>
                <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>{formatCurrency(projection.totalAssets || 0)}</strong></TableCell>
                <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>{formatCurrency(projection.netWorth || 0)}</strong></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Statistics */}
      <Paper sx={{ p: 2, mt: 2, bgcolor: 'primary.50' }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Total Years</Typography>
            <Typography variant="h6">{summary.yearly_projections.length}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Retirement Year</Typography>
            <Typography variant="h6">{summary.summary.user_retirement_year}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Starting Income</Typography>
            <Typography variant="h6">{formatCurrency(summary.yearly_projections[0]?.gross_income || 0)}</Typography>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Typography variant="caption" color="text.secondary">Final Year Income</Typography>
            <Typography variant="h6">{formatCurrency(summary.yearly_projections[summary.yearly_projections.length - 1]?.gross_income || 0)}</Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

