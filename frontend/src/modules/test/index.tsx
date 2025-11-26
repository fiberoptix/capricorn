/**
 * Test Module - QA Testing Dashboard
 * Provides visual testing of Tax API calculations
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Paper,
} from '@mui/material';
import {
  Science as ScienceIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';

// Tax calculation test configurations
const TAX_TESTS = [
  { state: 'NY', income: 300000, filingStatus: 'single', label: 'NY $300k Single' },
  { state: 'NY', income: 300000, filingStatus: 'married_filing_jointly', label: 'NY $300k Married Joint' },
  { state: 'NY', income: 300000, filingStatus: 'married_filing_separately', label: 'NY $300k Married Sep' },
  { state: 'NY', income: 500000, filingStatus: 'single', label: 'NY $500k Single' },
  { state: 'NY', income: 500000, filingStatus: 'married_filing_jointly', label: 'NY $500k Married Joint' },
  { state: 'NY', income: 500000, filingStatus: 'married_filing_separately', label: 'NY $500k Married Sep' },
  { state: 'FL', income: 300000, filingStatus: 'single', label: 'FL $300k Single' },
  { state: 'FL', income: 300000, filingStatus: 'married_filing_jointly', label: 'FL $300k Married Joint' },
  { state: 'FL', income: 300000, filingStatus: 'married_filing_separately', label: 'FL $300k Married Sep' },
];

interface TaxResult {
  gross_income: number;
  federal: {
    standard_deduction: number;
    taxable_income: number;
    tax: number;
    marginal_rate: number;
    effective_rate: number;
  };
  state: {
    state_code: string;
    standard_deduction: number;
    taxable_income: number;
    tax: number;
    marginal_rate: number;
    effective_rate: number;
  };
  local: {
    tax: number;
    rate: number;
  };
  total_tax: number;
  after_tax_income: number;
  effective_rate: number;
}

interface TestResult {
  config: typeof TAX_TESTS[0];
  result: TaxResult | null;
  error: string | null;
  loading: boolean;
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
};

const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

import { API_V1_URL } from '../../config/api';

// API base URL (dynamic based on hostname)
const API_BASE = API_V1_URL;

const TaxTestCard: React.FC<{ testResult: TestResult }> = ({ testResult }) => {
  const { config, result, error, loading } = testResult;
  const isFL = config.state === 'FL';

  return (
    <Card 
      sx={{ 
        height: '100%',
        border: '2px solid',
        borderColor: error ? 'error.main' : isFL ? 'success.main' : 'primary.main',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            {config.label}
          </Typography>
          <Chip 
            label={config.state} 
            color={isFL ? 'success' : 'primary'} 
            size="small"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>

        {/* Loading State */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Error State */}
        {error && (
          <Alert severity="error" icon={<ErrorIcon />} sx={{ mt: 1 }}>
            {error}
          </Alert>
        )}

        {/* Results */}
        {result && !loading && (
          <Box>
            {/* Income */}
            <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Gross Income
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                {formatCurrency(result.gross_income)}
              </Typography>
            </Box>

            <Divider sx={{ my: 1 }} />

            {/* Tax Breakdown */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {/* Federal */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Federal Tax</Typography>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    {formatCurrency(result.federal.tax)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatPercent(result.federal.effective_rate)} eff.
                  </Typography>
                </Box>
              </Box>

              {/* State */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">
                  State Tax ({result.state.state_code})
                </Typography>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: result.state.tax === 0 ? 'success.main' : 'inherit'
                    }}
                  >
                    {result.state.tax === 0 ? '$0 ✓' : formatCurrency(result.state.tax)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatPercent(result.state.effective_rate)} eff.
                  </Typography>
                </Box>
              </Box>

              {/* Local */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Local Tax</Typography>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatCurrency(result.local.tax)}
                </Typography>
              </Box>
            </Box>

            <Divider sx={{ my: 1 }} />

            {/* Total */}
            <Box sx={{ p: 1, bgcolor: 'primary.main', color: 'white', borderRadius: 1, mt: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  TOTAL TAX
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {formatCurrency(result.total_tax)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 0.5 }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Effective Rate
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  {formatPercent(result.effective_rate)}
                </Typography>
              </Box>
            </Box>

            {/* After Tax Income */}
            <Box sx={{ mt: 2, p: 1, bgcolor: 'success.light', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ color: 'success.dark' }}>
                  After-Tax Income
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.dark' }}>
                  {formatCurrency(result.after_tax_income)}
                </Typography>
              </Box>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export function TestModule() {
  const [testResults, setTestResults] = useState<TestResult[]>(
    TAX_TESTS.map((config) => ({
      config,
      result: null,
      error: null,
      loading: true,
    }))
  );

  useEffect(() => {
    const runTests = async () => {
      const results = await Promise.all(
        TAX_TESTS.map(async (config) => {
          try {
            const response = await fetch(`${API_BASE}/tax/income`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                income: config.income,
                filing_status: config.filingStatus,
                state: config.state,
                local_tax_rate: config.state === 'NY' ? 0.01 : 0, // 1% local for NY, 0% for FL
              }),
            });

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            return { config, result, error: null, loading: false };
          } catch (err) {
            return { 
              config, 
              result: null, 
              error: err instanceof Error ? err.message : 'Unknown error', 
              loading: false 
            };
          }
        })
      );

      setTestResults(results);
    };

    runTests();
  }, []);

  const successCount = testResults.filter(t => t.result && !t.error).length;
  const errorCount = testResults.filter(t => t.error).length;
  const loadingCount = testResults.filter(t => t.loading).length;

  return (
    <Box sx={{ p: 3, maxWidth: 1600, mx: 'auto' }}>
      {/* Header */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 3, 
          mb: 3, 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <ScienceIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              QA Test Dashboard
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Tax Calculation API Testing
            </Typography>
          </Box>
        </Box>

        {/* Status Summary */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Chip 
            icon={<CheckIcon />} 
            label={`${successCount} Passed`} 
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
          />
          {errorCount > 0 && (
            <Chip 
              icon={<ErrorIcon />} 
              label={`${errorCount} Failed`} 
              sx={{ bgcolor: 'rgba(255,0,0,0.3)', color: 'white' }}
            />
          )}
          {loadingCount > 0 && (
            <Chip 
              label={`${loadingCount} Running...`} 
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          )}
        </Box>
      </Paper>

      {/* Test Cards Grid */}
      <Grid container spacing={3}>
        {/* NY Section Header */}
        <Grid item xs={12}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
            🗽 New York (State Tax: Progressive)
          </Typography>
        </Grid>
        
        {/* NY Cards */}
        {testResults.slice(0, 6).map((testResult, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <TaxTestCard testResult={testResult} />
          </Grid>
        ))}

        {/* FL Section Header */}
        <Grid item xs={12} sx={{ mt: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'success.main', mb: 1 }}>
            🌴 Florida (No State Tax)
          </Typography>
        </Grid>

        {/* FL Cards */}
        {testResults.slice(6, 9).map((testResult, index) => (
          <Grid item xs={12} sm={6} md={4} key={index + 6}>
            <TaxTestCard testResult={testResult} />
          </Grid>
        ))}
      </Grid>

      {/* Footer Note */}
      <Paper sx={{ mt: 4, p: 2, bgcolor: 'grey.100' }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Test Configuration:</strong> Local tax rate is set to 1% for NY, 0% for FL. 
          All calculations use the centralized Tax API at <code>/api/v1/tax/income</code>.
        </Typography>
      </Paper>
    </Box>
  );
}

