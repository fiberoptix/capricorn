import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Grid,
  useTheme,
  ButtonGroup,
  Tooltip,
} from '@mui/material';
import {
  Timeline,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Visibility,
  VisibilityOff,
  RestartAlt,
} from '@mui/icons-material';

interface ChartDataPoint {
  date: string;
  categories: { [key: string]: number };
  cumulative: { [key: string]: number };
}

interface SummaryData {
  total_income: number;
  total_expenses: number;
  balance: number;
}

interface CumulativeSpendingChartProps {
  data: ChartDataPoint[];
  categories: string[];
  summary: SummaryData;
}

const CumulativeSpendingChart: React.FC<CumulativeSpendingChartProps> = ({
  data,
  categories,
  summary,
}) => {
  const theme = useTheme();
  const [visibleCategories, setVisibleCategories] = useState<Set<string>>(
    new Set(['Income', 'Expenses', 'Savings'])
  );
  const [chartMode, setChartMode] = useState<'net-income' | 'cash-flow'>('net-income');
  const [masterControl, setMasterControl] = useState<'show-all' | 'hide-all' | 'net-income' | 'cash-flow'>('net-income');

  // Ensure special summary categories are always available
  // Handle both string array and object array formats for categories
  const categoryNames = categories.map(cat => 
    typeof cat === 'string' ? cat : (cat?.name || cat)
  );
  const allCategories = [...new Set([...categoryNames, 'Income', 'Expenses', 'Savings'])];

  // Color palette for different categories
  const colorPalette = [
    theme.palette.success.main,     // Income - Green
    theme.palette.error.main,       // Expenses - Red
    theme.palette.secondary.main,   // Savings - Purple
    '#2196f3',  // Blue
    '#ff9800',  // Orange
    '#9c27b0',  // Purple
    '#00bcd4',  // Cyan
    '#4caf50',  // Light Green
    '#ff5722',  // Deep Orange
    '#607d8b',  // Blue Grey
    '#795548',  // Brown
    '#e91e63',  // Pink
    '#3f51b5',  // Indigo
    '#009688',  // Teal
    '#ffc107',  // Amber
    '#8bc34a',  // Light Green
    '#f44336',  // Red
    '#673ab7',  // Deep Purple
    '#cddc39',  // Lime
    '#ffeb3b',  // Yellow
  ];

  const getCategoryColor = (category: string, index: number) => {
    if (category === 'Income') return '#81c784';  // Light Green
    if (category === 'Expenses') return theme.palette.error.main;  // Red
    if (category === 'Savings') return '#2e7d32';  // Dark Green
    return colorPalette[index % colorPalette.length];
  };

  const toggleCategory = (category: string) => {
    const newVisible = new Set(visibleCategories);
    if (newVisible.has(category)) {
      newVisible.delete(category);
    } else {
      newVisible.add(category);
    }
    setVisibleCategories(newVisible);
  };

  const showAll = () => {
    // Show all categories EXCEPT Income, Expenses, and Savings (those are controlled by Net Income/Cash Flow buttons)
    const regularCategories = allCategories.filter(cat => !['Income', 'Expenses', 'Savings'].includes(cat));
    setVisibleCategories(new Set(regularCategories));
    setMasterControl('show-all');
  };

  const hideAll = () => {
    setVisibleCategories(new Set());
    setMasterControl('hide-all');
  };

  const showCashFlow = () => {
    setChartMode('cash-flow');
    setVisibleCategories(new Set(['Income', 'Expenses', 'Savings']));
    setMasterControl('cash-flow');
  };

  const showNetIncome = () => {
    setChartMode('net-income');
    setVisibleCategories(new Set(['Income', 'Expenses', 'Savings']));
    setMasterControl('net-income');
  };

  // Calculate monthly totals for Income, Expenses, and Savings
  const calculateMonthlyTotals = () => {
    if (!data || data.length === 0) return {};
    
    const monthlyTotals: { [key: string]: { income: number; expenses: number; savings: number } } = {};
    
    data.forEach(d => {
      if (d && d.date && d.categories) {
        const dateKey = d.date; // Use the date as the key
        
        if (!monthlyTotals[dateKey]) {
          monthlyTotals[dateKey] = { income: 0, expenses: 0, savings: 0 };
        }
        
        // Calculate totals for this date
        let dailyIncome = 0;
        let dailyExpenses = 0;
        
        Object.entries(d.categories).forEach(([category, amount]) => {
          if (amount && !isNaN(amount)) {
            if (amount > 0) {
              dailyIncome += Math.abs(amount);
            } else {
              dailyExpenses += Math.abs(amount);
            }
          }
        });
        
        monthlyTotals[dateKey].income = dailyIncome;
        monthlyTotals[dateKey].expenses = dailyExpenses;
        monthlyTotals[dateKey].savings = dailyIncome - dailyExpenses;
      }
    });
    
    return monthlyTotals;
  };

  const monthlyTotals = calculateMonthlyTotals();

  // Check if we have valid data
  if (!data || data.length === 0) {
    return (
      <Paper
        sx={{
          p: 3,
          background: 'linear-gradient(145deg, #ffffff 0%, #f8fdf8 100%)',
          border: '1px solid #e8f5e8',
          borderRadius: 2,
        }}
      >
        <Box display="flex" flexDirection="column" alignItems="center" gap={2} py={4}>
          <Timeline sx={{ color: theme.palette.text.secondary, fontSize: 48 }} />
          <Typography variant="h6" color="text.secondary">
            No transaction data available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please select a different time period or check your data.
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Calculate chart dimensions
  const chartWidth = 800;
  const chartHeight = 400;
  const padding = 60;
  const plotWidth = chartWidth - 2 * padding;
  const plotHeight = chartHeight - 2 * padding;

  // Calculate data range based on visible categories only
  const getVisibleValues = () => {
    if (visibleCategories.size === 0) return [0]; // If no categories visible, return default
    
    const allValues: number[] = [];
    
    // Handle special summary categories (same in both modes)
    if (visibleCategories.has('Income')) {
      if (chartMode === 'net-income') {
        // For Net Income mode, use cumulative values
        let cumulativeIncome = 0;
        data.forEach(d => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].income) : 0;
          cumulativeIncome += dailyValue;
          allValues.push(cumulativeIncome);
        });
      } else {
        // For Cash Flow mode, use daily values
        Object.values(monthlyTotals).forEach(totals => {
          allValues.push(Math.abs(totals.income));
        });
      }
    }
    
    if (visibleCategories.has('Expenses')) {
      if (chartMode === 'net-income') {
        // For Net Income mode, use cumulative values
        let cumulativeExpenses = 0;
        data.forEach(d => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].expenses) : 0;
          cumulativeExpenses += dailyValue;
          allValues.push(cumulativeExpenses);
        });
      } else {
        // For Cash Flow mode, use daily values
        Object.values(monthlyTotals).forEach(totals => {
          allValues.push(Math.abs(totals.expenses));
        });
      }
    }
    
    if (visibleCategories.has('Savings')) {
      if (chartMode === 'net-income') {
        // For Net Income mode, use cumulative values
        let cumulativeSavings = 0;
        data.forEach(d => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? monthlyTotals[dateKey].savings : 0;
          cumulativeSavings += dailyValue;
          allValues.push(cumulativeSavings);
        });
      } else {
        // For Cash Flow mode, use daily values
        Object.values(monthlyTotals).forEach(totals => {
          allValues.push(totals.savings);
        });
      }
    }
    
    // Handle regular categories (both modes)
    data.forEach(d => {
      if (d && d.categories) {
        visibleCategories.forEach(category => {
          if (category !== 'Income' && category !== 'Expenses' && category !== 'Savings') {
            const value = d.categories[category];
            if (value !== undefined && value !== null && !isNaN(value)) {
              allValues.push(Math.abs(value)); // Make all values positive
            }
          }
        });
      }
    });
    
    return allValues.length > 0 ? allValues : [0];
  };

  const visibleValues = getVisibleValues();
  const dataMax = Math.max(...visibleValues, 0);
  const dataMin = Math.min(...visibleValues, 0); // Allow negative values for savings

  // Calculate nice Y-axis scale with 10 ticks
  const calculateNiceScale = (min: number, max: number, tickCount: number = 10) => {
    const range = max - min;
    if (range === 0) return { min: min, max: max + 100, step: 10 }; // Fallback for no data
    
    const roughStep = range / (tickCount - 1);
    
    // Calculate nice step size
    const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
    const normalizedStep = roughStep / magnitude;
    
    let niceStep;
    if (normalizedStep <= 1) {
      niceStep = 1 * magnitude;
    } else if (normalizedStep <= 2) {
      niceStep = 2 * magnitude;
    } else if (normalizedStep <= 5) {
      niceStep = 5 * magnitude;
    } else {
      niceStep = 10 * magnitude;
    }
    
    // Calculate nice min and max
    const niceMin = Math.floor(min / niceStep) * niceStep;
    const niceMax = Math.ceil(max / niceStep) * niceStep;
    
    return { min: niceMin, max: niceMax, step: niceStep };
  };

  const { min: yMin, max: yMax, step: yStep } = calculateNiceScale(dataMin, dataMax, 10);
  const yRange = yMax - yMin;
  
  // Create Y-axis scale function with fallback
  const yScale = (value: number) => {
    if (isNaN(value) || value === undefined || value === null) {
      return chartHeight - padding; // Return bottom of chart for invalid values
    }
    return chartHeight - padding - ((value - yMin) / yRange) * plotHeight;
  };
  
  // Create X-axis scale function
  const xScale = (index: number) => 
    padding + (index / Math.max(data.length - 1, 1)) * plotWidth;

  // Generate Y-axis tick values
  const yTicks = [];
  for (let i = 0; i < 10; i++) {
    const tickValue = yMin + (yStep * i);
    if (!isNaN(tickValue)) {
      yTicks.push(tickValue);
    }
  }

  // Create path for each category
  const createPath = (category: string) => {
    if (chartMode === 'net-income') {
      // In Net Income mode, only handle Income, Expenses, and Savings as cumulative
      if (category === 'Income') {
        let cumulativeIncome = 0;
        const points = data.map((d, i) => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].income) : 0;
          cumulativeIncome += dailyValue;
          return {
            x: xScale(i),
            y: yScale(cumulativeIncome),
          };
        });
        return points.reduce((path, point, index) => {
          if (isNaN(point.x) || isNaN(point.y)) return path;
          if (index === 0) {
            return `M ${point.x} ${point.y}`;
          }
          return `${path} L ${point.x} ${point.y}`;
        }, '');
      }
      
      if (category === 'Expenses') {
        let cumulativeExpenses = 0;
        const points = data.map((d, i) => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].expenses) : 0;
          cumulativeExpenses += dailyValue;
          return {
            x: xScale(i),
            y: yScale(cumulativeExpenses),
          };
        });
        return points.reduce((path, point, index) => {
          if (isNaN(point.x) || isNaN(point.y)) return path;
          if (index === 0) {
            return `M ${point.x} ${point.y}`;
          }
          return `${path} L ${point.x} ${point.y}`;
        }, '');
      }
      
      if (category === 'Savings') {
        let cumulativeSavings = 0;
        const points = data.map((d, i) => {
          const dateKey = d.date;
          const dailyValue = monthlyTotals[dateKey] ? monthlyTotals[dateKey].savings : 0;
          cumulativeSavings += dailyValue;
          return {
            x: xScale(i),
            y: yScale(cumulativeSavings),
          };
        });
        return points.reduce((path, point, index) => {
          if (isNaN(point.x) || isNaN(point.y)) return path;
          if (index === 0) {
            return `M ${point.x} ${point.y}`;
          }
          return `${path} L ${point.x} ${point.y}`;
        }, '');
      }
      
      // In net-income mode, render regular categories as daily values
      const points = data.map((d, i) => {
        const value = d && d.categories && d.categories[category] ? Math.abs(d.categories[category]) : 0;
        return {
          x: xScale(i),
          y: yScale(value),
        };
      });
      
      return points.reduce((path, point, index) => {
        if (isNaN(point.x) || isNaN(point.y)) return path; // Skip invalid points
        if (index === 0) {
          return `M ${point.x} ${point.y}`;
        }
        return `${path} L ${point.x} ${point.y}`;
      }, '');
    } else {
      // In Cash Flow mode, handle all categories as daily values
      if (category === 'Income') {
        const points = data.map((d, i) => {
          const dateKey = d.date;
          const value = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].income) : 0;
          return {
            x: xScale(i),
            y: yScale(value),
          };
        });
        return points.reduce((path, point, index) => {
          if (isNaN(point.x) || isNaN(point.y)) return path;
          if (index === 0) {
            return `M ${point.x} ${point.y}`;
          }
          return `${path} L ${point.x} ${point.y}`;
        }, '');
      }
      
      if (category === 'Expenses') {
        const points = data.map((d, i) => {
          const dateKey = d.date;
          const value = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].expenses) : 0;
          return {
            x: xScale(i),
            y: yScale(value),
          };
        });
        return points.reduce((path, point, index) => {
          if (isNaN(point.x) || isNaN(point.y)) return path;
          if (index === 0) {
            return `M ${point.x} ${point.y}`;
          }
          return `${path} L ${point.x} ${point.y}`;
        }, '');
      }
      
             if (category === 'Savings') {
         const points = data.map((d, i) => {
           const dateKey = d.date;
           const value = monthlyTotals[dateKey] ? monthlyTotals[dateKey].savings : 0;
           return {
             x: xScale(i),
             y: yScale(value),
           };
         });
         return points.reduce((path, point, index) => {
           if (isNaN(point.x) || isNaN(point.y)) return path;
           if (index === 0) {
             return `M ${point.x} ${point.y}`;
           }
           return `${path} L ${point.x} ${point.y}`;
         }, '');
       }
      
      // Handle regular categories
      const points = data.map((d, i) => {
        const value = d && d.categories && d.categories[category] ? Math.abs(d.categories[category]) : 0;
        return {
          x: xScale(i),
          y: yScale(value),
        };
      });
      
      return points.reduce((path, point, index) => {
        if (isNaN(point.x) || isNaN(point.y)) return path; // Skip invalid points
        if (index === 0) {
          return `M ${point.x} ${point.y}`;
        }
        return `${path} L ${point.x} ${point.y}`;
      }, '');
    }
  };

  // Period buttons - REMOVED
  // const periodButtons = [
  //   { key: 'this_month', label: 'This Month' },
  //   { key: 'last_month', label: 'Last Month' },
  //   { key: 'last_3_months', label: 'Last 3 Months' },
  //   { key: 'this_year', label: 'This Year' },
  //   { key: 'all_time', label: 'All Time' },
  // ];

  return (
    <Paper
      sx={{
        p: 3,
        background: 'linear-gradient(145deg, #ffffff 0%, #f8fdf8 100%)',
        border: '1px solid #e8f5e8',
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box mb={3}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Timeline sx={{ color: theme.palette.primary.main }} />
          <Typography variant="h6" sx={{ 
            fontWeight: 600,
            color: 'primary.main',
          }}>
            {chartMode === 'net-income' ? 'Net Income Overview' : 'Transaction Amounts by Category'}
          </Typography>
        </Box>
        
        {/* Period Selector - REMOVED */}
        {/* <ButtonGroup variant="outlined" size="small" sx={{ mb: 2 }}>
          {periodButtons.map((btn) => (
            <Button
              key={btn.key}
              onClick={() => onPeriodChange(btn.key)}
              variant={period === btn.key ? 'contained' : 'outlined'}
              sx={{
                bgcolor: period === btn.key ? theme.palette.primary.main : 'transparent',
                color: period === btn.key ? 'white' : theme.palette.primary.main,
                '&:hover': {
                  bgcolor: period === btn.key ? theme.palette.primary.dark : 'rgba(46, 125, 50, 0.1)',
                },
              }}
            >
              {btn.label}
            </Button>
          ))}
        </ButtonGroup> */}
      </Box>

      {/* Chart */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <svg width={chartWidth} height={chartHeight} style={{ background: 'white', borderRadius: 8 }}>
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f0f0f0" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Y-axis labels */}
          {yTicks.map((tickValue, index) => {
            const y = yScale(tickValue);
            if (isNaN(y)) return null; // Skip if invalid
            return (
              <g key={index}>
                <line
                  x1={padding - 5}
                  y1={y}
                  x2={padding}
                  y2={y}
                  stroke={theme.palette.text.secondary}
                  strokeWidth="1"
                />
                <text
                  x={padding - 10}
                  y={y + 5}
                  textAnchor="end"
                  fontSize="12"
                  fill={theme.palette.text.secondary}
                >
                  ${tickValue.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                </text>
              </g>
            );
          })}
          
          {/* X-axis labels */}
          {data.map((d, i) => {
            if (i % Math.ceil(data.length / 8) === 0) {
              const x = xScale(i);
              if (isNaN(x)) return null; // Skip if invalid
              return (
                <g key={i}>
                  <line
                    x1={x}
                    y1={chartHeight - padding}
                    x2={x}
                    y2={chartHeight - padding + 5}
                    stroke={theme.palette.text.secondary}
                    strokeWidth="1"
                  />
                  <text
                    x={x}
                    y={chartHeight - padding + 20}
                    textAnchor="middle"
                    fontSize="12"
                    fill={theme.palette.text.secondary}
                  >
                    {d && d.date ? new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
                  </text>
                </g>
              );
            }
            return null;
          })}
          
          {/* Category lines */}
          {allCategories.map((category, index) => {
            if (!visibleCategories.has(category)) return null;
            
            const color = getCategoryColor(category, index);
            const path = createPath(category);
            
            if (!path) return null; // Skip if no valid path
            
            return (
              <g key={category}>
                <path
                  d={path}
                  fill="none"
                  stroke={color}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Data points - only show in Cash Flow mode */}
                {chartMode === 'cash-flow' && data.map((d, i) => {
                  let value, x, y;
                  
                  // Handle special summary categories using monthly calculations
                  if (category === 'Income') {
                    const dateKey = d.date;
                    value = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].income) : 0;
                  } else if (category === 'Expenses') {
                    const dateKey = d.date;
                    value = monthlyTotals[dateKey] ? Math.abs(monthlyTotals[dateKey].expenses) : 0;
                  } else if (category === 'Savings') {
                    const dateKey = d.date;
                    value = monthlyTotals[dateKey] ? monthlyTotals[dateKey].savings : 0;
                  } else {
                    // Handle regular categories
                    value = d && d.categories && d.categories[category] ? Math.abs(d.categories[category]) : 0;
                  }
                  
                  x = xScale(i);
                  y = yScale(value);
                  
                  if (isNaN(x) || isNaN(y)) return null; // Skip invalid points
                  
                  return (
                    <circle
                      key={i}
                      cx={x}
                      cy={y}
                      r="4"
                      fill={color}
                      stroke="white"
                      strokeWidth="2"
                    />
                  );
                })}
              </g>
            );
          })}
          
          {/* Axes */}
          <line
            x1={padding}
            y1={chartHeight - padding}
            x2={chartWidth - padding}
            y2={chartHeight - padding}
            stroke={theme.palette.text.secondary}
            strokeWidth="2"
          />
          <line
            x1={padding}
            y1={padding}
            x2={padding}
            y2={chartHeight - padding}
            stroke={theme.palette.text.secondary}
            strokeWidth="2"
          />
        </svg>
      </Box>

      {/* Master Controls */}
      <Box mb={3}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Master Controls
        </Typography>
        <ButtonGroup variant="outlined" size="small">
          <Button
            onClick={showAll}
            startIcon={<Visibility />}
            sx={{ 
              color: theme.palette.primary.main,
              backgroundColor: masterControl === 'show-all' ? theme.palette.primary.light : 'transparent',
              '&:hover': {
                backgroundColor: masterControl === 'show-all' ? theme.palette.primary.light : theme.palette.action.hover,
              }
            }}
          >
            Show All
          </Button>
          <Button
            onClick={hideAll}
            startIcon={<VisibilityOff />}
            sx={{ 
              color: theme.palette.primary.main,
              backgroundColor: masterControl === 'hide-all' ? theme.palette.primary.light : 'transparent',
              '&:hover': {
                backgroundColor: masterControl === 'hide-all' ? theme.palette.primary.light : theme.palette.action.hover,
              }
            }}
          >
            Hide All
          </Button>
          <Button
            onClick={showNetIncome}
            startIcon={<TrendingUp />}
            sx={{ 
              color: theme.palette.primary.main,
              backgroundColor: masterControl === 'net-income' ? theme.palette.primary.light : 'transparent',
              '&:hover': {
                backgroundColor: masterControl === 'net-income' ? theme.palette.primary.light : theme.palette.action.hover,
              }
            }}
          >
            Net Income
          </Button>
          <Button
            onClick={showCashFlow}
            startIcon={<RestartAlt />}
            sx={{ 
              color: theme.palette.primary.main,
              backgroundColor: masterControl === 'cash-flow' ? theme.palette.primary.light : 'transparent',
              '&:hover': {
                backgroundColor: masterControl === 'cash-flow' ? theme.palette.primary.light : theme.palette.action.hover,
              }
            }}
          >
            Cash Flow
          </Button>
        </ButtonGroup>
      </Box>

      {/* Category Toggle Controls */}
      <Box>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Category Controls
        </Typography>
        <Grid container spacing={1}>
          {allCategories.map((category, index) => (
            <Grid item key={category}>
              <Tooltip title={`Toggle ${category}`} arrow>
                <Chip
                  label={category}
                  onClick={() => toggleCategory(category)}
                  sx={{
                    backgroundColor: visibleCategories.has(category) 
                      ? getCategoryColor(category, index) 
                      : theme.palette.grey[200],
                    color: visibleCategories.has(category) 
                      ? 'white' 
                      : theme.palette.text.secondary,
                    fontWeight: visibleCategories.has(category) ? 600 : 400,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                    },
                  }}
                />
              </Tooltip>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Paper>
  );
};

export default CumulativeSpendingChart; 