import React from 'react';
import { Box, Paper, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import { GitHub, Launch, Code, Description } from '@mui/icons-material';

export const HelpModule: React.FC = () => {
  return (
    <Box sx={{ p: 2 }}>
      {/* Banner */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
          color: 'white',
          borderRadius: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Description sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Help & About
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Capricorn - Open source personal finance platform
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Content */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <GitHub sx={{ fontSize: 32, color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  GitHub Repository
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
                Capricorn is open source software released under the MIT License. Visit the GitHub repository for:
              </Typography>
              <Box component="ul" sx={{ mb: 3, pl: 2 }}>
                <li>Source code and documentation</li>
                <li>Installation instructions</li>
                <li>Feature requests and bug reports</li>
                <li>Contribution guidelines</li>
                <li>Latest releases and updates</li>
              </Box>
              <Button
                variant="contained"
                startIcon={<Launch />}
                href="https://github.com/fiberoptix/capricorn"
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                  },
                }}
              >
                View on GitHub
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Code sx={{ fontSize: 32, color: '#6366f1' }} />
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  About Capricorn
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
                Capricorn is a unified personal finance platform that combines:
              </Typography>
              <Box component="ul" sx={{ mb: 2, pl: 2 }}>
                <li><strong>Finance Manager:</strong> Track transactions with 97% ML auto-categorization</li>
                <li><strong>Portfolio Manager:</strong> Investment tracking with tax-aware break-even analysis</li>
                <li><strong>Retirement Planner:</strong> 30-year projections with asset growth modeling</li>
                <li><strong>Tax Calculator:</strong> State comparison with progressive tax rates</li>
              </Box>
              <Typography variant="body2" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                Built with FastAPI, React, PostgreSQL, and deployed with Docker.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2 }}>
                📦 Demo Data
              </Typography>
              <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
                This instance is pre-loaded with demo data featuring Bob & Mary Smith:
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      559
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Transactions
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      3
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Portfolios
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      27
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Months of Data
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      2024-2026
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Date Range
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
                Use the <strong>Data</strong> tab to export, import, or clear this demo data. You can replace it with your own data anytime.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Footer Tip */}
      <Paper sx={{ mt: 3, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Capricorn is designed for single-user home lab deployments. All data is stored locally in your PostgreSQL database.
        </Typography>
      </Paper>
    </Box>
  );
};

