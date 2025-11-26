/**
 * Asset Growth View
 * Displays asset growth projections over time
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

export function AssetGrowthView() {
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
        Failed to load asset growth: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!summary || !summary.asset_growth) {
    return <Alert severity="info">No asset growth data available</Alert>;
  }

  const formatCurrency = (amount: number) => `$${Math.round(amount).toLocaleString()}`;

  const finalAssets = summary.asset_growth[summary.asset_growth.length - 1];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        💰 Asset Growth Over Time
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Track how your retirement accounts grow over 30 years
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">{userName} 401K Final</Typography>
            <Typography variant="h6" color="primary">{formatCurrency(finalAssets.userAccount401k)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">Trading Account</Typography>
            <Typography variant="h6" color="success.main">{formatCurrency(finalAssets.accountTrading)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">Total Saved</Typography>
            <Typography variant="h6" color="info.main">{formatCurrency(finalAssets.cumulativeSavings)}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">Total Assets</Typography>
            <Typography variant="h6" color="secondary.main">{formatCurrency(finalAssets.totalAssets)}</Typography>
          </Paper>
        </Grid>
      </Grid>

      <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ position: 'sticky', left: 0, bgcolor: 'background.paper', zIndex: 3 }}><strong>Year</strong></TableCell>
              <TableCell align="right"><strong>{userName} 401K</strong></TableCell>
              <TableCell align="right"><strong>{partnerName} 401K</strong></TableCell>
              <TableCell align="right"><strong>IRA Account</strong></TableCell>
              <TableCell align="right"><strong>Savings Account</strong></TableCell>
              <TableCell align="right"><strong>Trading Account</strong></TableCell>
              <TableCell align="right"><strong>Inheritance</strong></TableCell>
              <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>Total Assets</strong></TableCell>
              <TableCell align="right"><strong>Annual Growth</strong></TableCell>
              <TableCell align="right"><strong>Cumulative Saved</strong></TableCell>
              <TableCell align="right"><strong>Uninvested Surplus</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {summary.asset_growth.map((growth, idx) => (
              <TableRow 
                key={growth.year} 
                hover
                sx={{ 
                  bgcolor: idx === summary.asset_growth.length - 1 ? 'success.50' : 'inherit' 
                }}
              >
                <TableCell sx={{ position: 'sticky', left: 0, bgcolor: idx === summary.asset_growth.length - 1 ? 'success.50' : 'background.paper', zIndex: 1 }}>
                  {growth.year}
                </TableCell>
                <TableCell align="right">{formatCurrency(growth.userAccount401k)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.partnerAccount401k)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.accountIRA)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.accountSavings)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.accountTrading)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.inheritance)}</TableCell>
                <TableCell align="right" sx={{ bgcolor: 'success.50' }}><strong>{formatCurrency(growth.totalAssets)}</strong></TableCell>
                <TableCell align="right" sx={{ color: growth.annualGrowth >= 0 ? 'success.main' : 'error.main' }}>
                  {formatCurrency(growth.annualGrowth)}
                </TableCell>
                <TableCell align="right">{formatCurrency(growth.cumulativeSavings)}</TableCell>
                <TableCell align="right">{formatCurrency(growth.uninvestedSurplus)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

