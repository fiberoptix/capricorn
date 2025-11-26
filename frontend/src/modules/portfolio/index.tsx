/**
 * Portfolio Module Main Component - Standardized UI/UX
 * 
 * Using TAXES/TEST style with blue gradient header
 */

import React, { useState } from 'react';
import { Box, Tabs, Tab, Paper, Typography } from '@mui/material';
import { ShowChart as PortfolioIcon } from '@mui/icons-material';

// Import Portfolio components/pages
import PortfolioOverview from './components/PortfolioOverview';
import { MarketPricesTab } from './components/market-prices/market-prices-tab';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`portfolio-tabpanel-${index}`}
      aria-labelledby={`portfolio-tab-${index}`}
      {...other}
    >
      {value === index && children}
    </div>
  );
}

export function PortfolioModule() {
  const [activeTab, setActiveTab] = useState(0);

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Sub-tabs bar FIRST - matching Finance pattern */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleChange} 
          aria-label="portfolio tabs"
          sx={{ 
            '& .MuiTab-root': {
              textTransform: 'none',
              minWidth: 100,
            }
          }}
        >
          <Tab label="Overview" />
          <Tab label="Market Prices" />
        </Tabs>
      </Box>
      
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ p: 2 }}>
          {/* Banner inside content - matching Finance pattern */}
          <Paper 
            sx={{ 
              p: 3, 
              mb: 3,
              background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
              color: 'white',
              borderRadius: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PortfolioIcon sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  Portfolio Manager
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.9 }}>
                  Track your investments, market prices, and tax exposure
                </Typography>
              </Box>
            </Box>
          </Paper>
          <PortfolioOverview />
        </Box>
      </TabPanel>
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ p: 2 }}>
          <MarketPricesTab />
        </Box>
      </TabPanel>
    </Box>
  );
}

export default PortfolioModule;
