// Finance Module Main Component
import React, { useState } from 'react';
import { Box, Tabs, Tab, Typography } from '@mui/material';

// Import Finance pages
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Budget from './pages/Budget';
import Upload from './pages/Upload';
import Settings from './pages/Settings';

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
      id={`finance-tabpanel-${index}`}
      aria-labelledby={`finance-tab-${index}`}
      {...other}
    >
      {value === index && children}
    </div>
  );
}

export function FinanceModule() {
  const [activeTab, setActiveTab] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleChange} 
          aria-label="finance tabs"
          sx={{ 
            '& .MuiTab-root': {
              textTransform: 'none',
              minWidth: 100,
            }
          }}
        >
          <Tab label="Dashboard" />
          <Tab label="Transactions" />
          <Tab label="Budget" />
          <Tab label="Upload" />
          <Tab label="Settings" />
        </Tabs>
      </Box>
      
      <TabPanel value={activeTab} index={0}>
        <Dashboard />
      </TabPanel>
      <TabPanel value={activeTab} index={1}>
        <Transactions />
      </TabPanel>
      <TabPanel value={activeTab} index={2}>
        <Budget />
      </TabPanel>
      <TabPanel value={activeTab} index={3}>
        <Upload />
      </TabPanel>
      <TabPanel value={activeTab} index={4}>
        <Settings />
      </TabPanel>
    </Box>
  );
}

export default FinanceModule;
