import React, { useState } from 'react';
import { Box, Tabs, Tab, Link } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import { Banner } from './Banner';
import { Dashboard } from '../pages/Dashboard';
import { FinanceModule } from '../modules/finance';
import { TaxesModule } from '../modules/taxes';
import { PortfolioModule } from '../modules/portfolio';
import { ProfileModule } from '../modules/profile';
import { RetirementModule } from '../modules/retirement';
import { DataModule } from '../modules/data';

const TABS = ['Dashboard', 'Finance', 'Taxes', 'Portfolio', 'Retirement', 'Profile', 'Data'];
const GITHUB_URL = 'https://github.com/fiberoptix/capricorn';

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
      
      <Box sx={{ display: 'flex', borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{ px: 2, flex: 1 }}
        >
          {TABS.map((tab) => (
            <Tab key={tab} label={tab} />
          ))}
        </Tabs>
        
        <Link
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            px: 2,
            color: 'text.secondary',
            textDecoration: 'none',
            fontSize: '0.875rem',
            '&:hover': {
              color: 'primary.main',
            },
          }}
        >
          <GitHubIcon sx={{ fontSize: 18 }} />
          Help & About
        </Link>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', bgcolor: 'background.default' }}>
        {renderContent()}
      </Box>
    </Box>
  );
};

