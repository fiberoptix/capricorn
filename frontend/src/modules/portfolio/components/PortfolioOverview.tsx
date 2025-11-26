/**
 * Portfolio Overview Component - Standardized UI/UX
 * 
 * Main portfolio dashboard showing all portfolios and summary
 * Matches TAXES/TEST style
 */

import React, { useState, useEffect } from 'react';
import { 
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Divider,
  Paper
} from '@mui/material';
import { 
  Add as AddIcon,
  Edit as EditIcon,
  TrendingUp,
  AccountBalance,
  ShowChart,
  AttachMoney,
  BusinessCenter,
} from '@mui/icons-material';
import { API_V1_URL } from '../../../config/api';
import {
  ArrowBack,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Savings as SavingsIcon
} from '@mui/icons-material';
import { usePortfolios, useCreatePortfolio, useUpdatePortfolio, useDeletePortfolio } from '../hooks/use-portfolios';
import { PortfolioForm } from './forms/portfolio-form';
import { PortfolioDetail } from './portfolio/portfolio-detail';
import { useInvestorProfiles } from '../hooks/use-investor-profiles';
import { api } from '../lib/api-client';

// Format currency
const formatCurrency = (value: number) => 
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

// Summary Card Component
interface SummaryCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error';
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, value, icon, color = 'primary' }) => {
  const colorMap = {
    primary: { bg: 'primary.50', text: 'primary.main' },
    success: { bg: 'success.light', text: 'success.dark' },
    warning: { bg: 'warning.light', text: 'warning.dark' },
    error: { bg: 'error.light', text: 'error.dark' },
  };
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ 
            p: 1, 
            borderRadius: 1, 
            bgcolor: colorMap[color].bg,
            color: colorMap[color].text,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {icon}
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: colorMap[color].text }}>
              {value}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

// Portfolio Card Component
interface PortfolioCardProps {
  portfolio: any;
  onView: () => void;
  onEdit: () => void;
}

const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio, onView, onEdit }) => {
  const isRetirement = portfolio.type === 'retirement' || portfolio.type === '401k' || portfolio.type === 'IRA';
  const hasGains = (portfolio.total_unrealized_gains || 0) > 0;
  
  return (
    <Card sx={{ 
      height: '100%',
      border: '2px solid',
      borderColor: isRetirement ? 'secondary.main' : 'primary.main',
      transition: 'transform 0.2s, box-shadow 0.2s',
      '&:hover': {
        transform: 'translateY(-2px)',
        boxShadow: 4,
      },
    }}>
      <CardContent sx={{ p: 2 }}>
        {/* Header with badge and edit */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isRetirement ? (
              <AccountBalance sx={{ color: 'secondary.main' }} />
            ) : (
              <ShowChart sx={{ color: 'primary.main' }} />
            )}
            <Chip
              label={portfolio.type}
              size="small"
              color={isRetirement ? 'secondary' : 'primary'}
              sx={{ fontWeight: 'bold', fontSize: '0.7rem' }}
            />
          </Box>
          <IconButton size="small" onClick={onEdit}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Box>

        {/* Name */}
        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
          {portfolio.name}
        </Typography>

        {/* Stats Grid */}
        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">Value</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {formatCurrency(portfolio.total_value || 0)}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">Unrealized Gains</Typography>
            <Typography 
              variant="body1" 
              sx={{ fontWeight: 'bold', color: hasGains ? 'success.main' : 'error.main' }}
            >
              {formatCurrency(portfolio.total_unrealized_gains || 0)}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">Cash</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {formatCurrency(portfolio.cash_on_hand || 0)}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">Break-Even</Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              {(portfolio.avg_break_even || 0).toFixed(1)}%
            </Typography>
          </Grid>
        </Grid>

        {/* View Details Button */}
        <Button
          variant="outlined"
          fullWidth
          size="small"
          onClick={onView}
          sx={{ mt: 2 }}
        >
          View Details →
        </Button>
      </CardContent>
    </Card>
  );
};

export default function PortfolioOverview() {
  const { data: portfolios, isLoading, error, refetch } = usePortfolios();
  const createPortfolio = useCreatePortfolio();
  const updatePortfolio = useUpdatePortfolio();
  const deletePortfolio = useDeletePortfolio();
  const { data: profiles } = useInvestorProfiles();
  
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingPortfolio, setEditingPortfolio] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);

  // Calculate summary data
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch(`${API_V1_URL}/portfolio/summary`);
        if (response.ok) {
          const data = await response.json();
          setSummaryData(data);
        }
      } catch (error) {
        console.error('Failed to fetch portfolio summary:', error);
      }
    };
    
    fetchSummary();
  }, [portfolios]);

  const handleCreatePortfolio = () => {
    setEditingPortfolio(null);
    setIsFormOpen(true);
  };

  const handleEditPortfolio = (portfolio: any) => {
    setEditingPortfolio(portfolio);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (data: any) => {
    try {
      if (editingPortfolio) {
        await updatePortfolio.mutateAsync({
          id: editingPortfolio.id,
          ...data
        });
      } else {
        await createPortfolio.mutateAsync(data);
      }
      setIsFormOpen(false);
      refetch();
    } catch (error) {
      console.error('Error saving portfolio:', error);
    }
  };

  const handleDeletePortfolio = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this portfolio?')) {
      try {
        await deletePortfolio.mutateAsync(id);
        if (selectedPortfolioId === id) {
          setSelectedPortfolioId(null);
        }
        refetch();
      } catch (error) {
        console.error('Error deleting portfolio:', error);
      }
    }
  };

  const handleViewDetails = (portfolioId: number) => {
    setSelectedPortfolioId(portfolioId);
  };

  const handleBackToOverview = () => {
    setSelectedPortfolioId(null);
  };

  // If a portfolio is selected, show the detail view
  if (selectedPortfolioId) {
    return (
      <Box>
        <Button 
          startIcon={<ArrowBack />}
          onClick={handleBackToOverview}
          sx={{ mb: 2 }}
          variant="outlined"
        >
          Back to Overview
        </Button>
        <PortfolioDetail 
          portfolioId={selectedPortfolioId}
          investorProfileId={profiles?.[0]?.id}
        />
      </Box>
    );
  }

  return (
    <Box>
      {/* Summary Cards */}
      {summaryData && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2.4}>
            <SummaryCard 
              label="Total Value"
              value={formatCurrency(summaryData.total_value || 0)}
              icon={<AttachMoney />}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <SummaryCard 
              label="Securities Value"
              value={formatCurrency(summaryData.securities_value || 0)}
              icon={<TrendingUp />}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <SummaryCard 
              label="Tax Liability"
              value={formatCurrency(summaryData.tax_liability || 0)}
              icon={<WarningIcon />}
              color="warning"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <SummaryCard 
              label="After-Tax Value"
              value={formatCurrency(summaryData.after_tax_value || 0)}
              icon={<CheckCircleIcon />}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2.4}>
            <SummaryCard 
              label="Cash on Hand"
              value={formatCurrency(summaryData.cash_on_hand || 0)}
              icon={<SavingsIcon />}
              color="success"
            />
          </Grid>
        </Grid>
      )}

      {/* Portfolios Section */}
      <Card>
        <CardContent sx={{ p: 2 }}>
          {/* Section Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ 
              display: 'inline-block',
              bgcolor: 'primary.main',
              color: 'white',
              px: 2,
              py: 0.5,
              borderRadius: 1,
              fontSize: '0.85rem',
              fontWeight: 'bold',
            }}>
              📊 Your Portfolios
            </Box>
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={handleCreatePortfolio}
            >
              New Portfolio
            </Button>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : error ? (
            <Alert severity="error">
              Error loading portfolios: {error.message}
            </Alert>
          ) : !portfolios || portfolios.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <BusinessCenter sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Portfolios Yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Create your first portfolio to start tracking your investments
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleCreatePortfolio}
              >
                Create Portfolio
              </Button>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {portfolios.map((portfolio) => (
                <Grid item xs={12} sm={6} md={4} key={portfolio.id}>
                  <PortfolioCard
                    portfolio={portfolio}
                    onView={() => handleViewDetails(portfolio.id)}
                    onEdit={() => handleEditPortfolio(portfolio)}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </CardContent>
      </Card>

      {/* Footer Note */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Note:</strong> Tax calculations use your Profile settings (state, filing status, local tax). 
          Break-even analysis shows how much a position can drop before losing money after taxes.
        </Typography>
      </Paper>

      {/* Portfolio Form Modal */}
      {isFormOpen && (
        <PortfolioForm
          isOpen={isFormOpen}
          onClose={() => setIsFormOpen(false)}
          onSubmit={handleFormSubmit}
          initialData={editingPortfolio}
          onDelete={editingPortfolio ? () => handleDeletePortfolio(editingPortfolio.id) : undefined}
        />
      )}
    </Box>
  );
}
