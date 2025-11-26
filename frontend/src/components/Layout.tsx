import React, { useState } from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import { Banner } from './Banner';
import { Dashboard } from '../pages/Dashboard';
import { FinanceModule } from '../modules/finance';
import { TaxesModule } from '../modules/taxes';
import { PortfolioModule } from '../modules/portfolio';
import { ProfileModule } from '../modules/profile';
import { RetirementModule } from '../modules/retirement';
import { DataModule } from '../modules/data';

const TABS = ['Dashboard', 'Finance', 'Taxes', 'Portfolio', 'Retirement', 'Profile', 'Data'];

export const Layout: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 0:
        return <Dashboard />;
      case 1:
        return <FinanceModule />;
      case 2:
        return <TaxesModule />;
      case 3:
        return <PortfolioModule />;
      case 4:
        return <RetirementModule />;
      case 5:
        return <ProfileModule />;
      case 6:
        return <DataModule />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Banner />
      
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          px: 2,
        }}
      >
        {TABS.map((tab) => (
          <Tab key={tab} label={tab} />
        ))}
      </Tabs>

      <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'background.default' }}>
        {renderContent()}
      </Box>
    </Box>
  );
};

