/**
 * Asset Growth Chart Component
 * Interactive line chart showing asset growth over time
 */
import React, { useState } from 'react';
import { Box, Paper, Typography, Button, ButtonGroup } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AssetGrowth } from '../types/retirement.types';

interface AssetGrowthChartProps {
  data: AssetGrowth[];
  userName?: string;
  partnerName?: string;
}

export function AssetGrowthChart({ data, userName = 'User', partnerName = 'Partner' }: AssetGrowthChartProps) {
  const [visibleSeries, setVisibleSeries] = useState<Set<string>>(
    new Set(['totalAssets', 'userAccount401k', 'partnerAccount401k', 'accountIRA', 'accountTrading'])
  );

  const toggleSeries = (series: string) => {
    setVisibleSeries((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(series)) {
        newSet.delete(series);
      } else {
        newSet.add(series);
      }
      return newSet;
    });
  };

  const showAll = () => {
    setVisibleSeries(new Set([
      'totalAssets', 'userAccount401k', 'partnerAccount401k', 'accountIRA',
      'accountSavings', 'accountTrading', 'inheritance', 'cumulativeSavings',
      'annualGrowth', 'uninvestedSurplus'
    ]));
  };

  const hideAll = () => {
    setVisibleSeries(new Set());
  };

  const showMainAccounts = () => {
    setVisibleSeries(new Set(['totalAssets', 'userAccount401k', 'partnerAccount401k', 'accountIRA', 'accountTrading']));
  };

  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const seriesConfig = [
    { key: 'totalAssets', label: 'Total Assets', color: '#2196F3' },
    { key: 'userAccount401k', label: `${userName} 401K Account`, color: '#1565C0' },
    { key: 'partnerAccount401k', label: `${partnerName} 401K Account`, color: '#1976D2' },
    { key: 'accountIRA', label: 'IRA Account', color: '#42A5F5' },
    { key: 'accountSavings', label: 'Savings Account', color: '#90CAF9' },
    { key: 'accountTrading', label: 'Trading Account', color: '#4CAF50' },
    { key: 'inheritance', label: 'Inheritance', color: '#FF9800' },
    { key: 'cumulativeSavings', label: 'Cumulative Saved', color: '#9C27B0' },
    { key: 'annualGrowth', label: 'Annual Growth', color: '#F44336' },
    { key: 'uninvestedSurplus', label: 'Uninvested Surplus', color: '#607D8B' },
  ];

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        📈 Asset Growth Over Time
      </Typography>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="year" />
          <YAxis tickFormatter={formatCurrency} />
          <Tooltip formatter={(value: number) => formatCurrency(value)} />
          <Legend />
          {seriesConfig.map((series) =>
            visibleSeries.has(series.key) ? (
              <Line
                key={series.key}
                type="monotone"
                dataKey={series.key}
                stroke={series.color}
                strokeWidth={series.key === 'totalAssets' ? 3 : 2}
                dot={false}
                name={series.label}
              />
            ) : null
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Data Series Controls */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Data Series Controls:
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          {seriesConfig.map((series) => (
            <Button
              key={series.key}
              variant={visibleSeries.has(series.key) ? 'contained' : 'outlined'}
              size="small"
              onClick={() => toggleSeries(series.key)}
              sx={{ 
                bgcolor: visibleSeries.has(series.key) ? series.color : 'transparent',
                borderColor: series.color,
                color: visibleSeries.has(series.key) ? 'white' : series.color,
                '&:hover': {
                  bgcolor: series.color,
                  color: 'white',
                }
              }}
            >
              {series.label}
            </Button>
          ))}
        </Box>

        {/* Quick Actions */}
        <ButtonGroup size="small">
          <Button onClick={showAll}>Show All</Button>
          <Button onClick={hideAll}>Hide All</Button>
          <Button onClick={showMainAccounts}>Show Main Accounts</Button>
        </ButtonGroup>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          Currently showing: {Array.from(visibleSeries).map(s => 
            seriesConfig.find(c => c.key === s)?.label
          ).filter(Boolean).join(', ')}
        </Typography>
      </Box>
    </Paper>
  );
}

