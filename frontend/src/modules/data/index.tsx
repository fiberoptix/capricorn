/**
 * DATA Module - Export/Import All User Data
 * Phase 10: Full backup and restore functionality
 */

import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Upload as UploadIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery, useQueryClient } from '@tanstack/react-query';

import { API_V1_URL } from '../../config/api';

// API base URL (dynamic based on hostname)
const API_BASE = API_V1_URL;

interface DataCounts {
  user_profile: number;
  accounts: number;
  categories: number;
  transactions: number;
  portfolios: number;
  portfolio_transactions: number;
  market_prices: number;
  investor_profiles: number;
  total: number;
}

export const DataModule: React.FC = () => {
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showClearDialog, setShowClearDialog] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch current data counts
  const { data: summaryData, isLoading: isLoadingSummary, refetch: refetchSummary } = useQuery({
    queryKey: ['dataSummary'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/data/summary`);
      if (!response.ok) throw new Error('Failed to fetch summary');
      return response.json();
    },
  });

  const counts: DataCounts = summaryData?.counts || {
    user_profile: 0,
    accounts: 0,
    categories: 0,
    transactions: 0,
    portfolios: 0,
    portfolio_transactions: 0,
    market_prices: 0,
    investor_profiles: 0,
    total: 0,
  };

  // Calculate user data count (excluding bootstrap profile records)
  const userDataCount = counts.accounts + counts.categories + counts.transactions + 
                        counts.portfolios + counts.portfolio_transactions + counts.market_prices;

  // Handle export
  const handleExport = async () => {
    setIsExporting(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_BASE}/data/export`);
      if (!response.ok) throw new Error('Export failed');
      
      // Get the blob and download
      const blob = await response.blob();
      
      // Generate filename with timestamp: Capricorn_UserData_YYYY-MM-DD_HHMM.json
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const filename = `Capricorn_UserData_${year}-${month}-${day}_${hours}${minutes}.json`;
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setMessage({ type: 'success', text: `Exported ${userDataCount.toLocaleString()} records + profile settings successfully!` });
    } catch (error) {
      setMessage({ type: 'error', text: `Export failed: ${error}` });
    } finally {
      setIsExporting(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        setMessage({ type: 'error', text: 'Please select a JSON file' });
        return;
      }
      setImportFile(file);
      setShowConfirmDialog(true);
    }
  };

  // Handle import confirmation
  const handleImportConfirm = async () => {
    if (!importFile) return;
    
    setShowConfirmDialog(false);
    setIsImporting(true);
    setMessage(null);
    
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      
      const response = await fetch(`${API_BASE}/data/import`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Import failed');
      }
      
      const result = await response.json();
      
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries();
      
      // Refetch summary
      await refetchSummary();
      
      setMessage({ 
        type: 'success', 
        text: `Imported ${result.imported.total} records successfully! Refresh other tabs to see updated data.` 
      });
    } catch (error) {
      setMessage({ type: 'error', text: `Import failed: ${error}` });
    } finally {
      setIsImporting(false);
      setImportFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle import cancel
  const handleImportCancel = () => {
    setShowConfirmDialog(false);
    setImportFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle clear all data
  const handleClearData = async () => {
    setShowClearDialog(false);
    setIsClearing(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_BASE}/data/clear`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Clear failed');
      }
      
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries();
      
      // Refetch summary
      await refetchSummary();
      
      setMessage({ 
        type: 'success', 
        text: 'All user data has been cleared successfully.' 
      });
    } catch (error) {
      setMessage({ type: 'error', text: `Clear failed: ${error}` });
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #6366f1, #4f46e5)', 
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StorageIcon sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              📦 Data Management
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Export and import your complete Capricorn data for backup or migration
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Message Alert */}
      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 3 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Current Database Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
            <Box sx={{ 
              background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
              color: 'white',
              px: 2,
              py: 1.5,
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}>
              <Box sx={{ fontSize: 20 }}>📊</Box>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Current Database
              </Typography>
            </Box>
            <CardContent>
              {isLoadingSummary ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Box>
                  {/* User Data Section */}
                  <Typography variant="caption" sx={{ color: '#6b7280', fontWeight: 'bold', textTransform: 'uppercase', mb: 1, display: 'block' }}>
                    User Data
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Accounts</Typography>
                    <Typography sx={{ fontWeight: 'bold' }}>{counts.accounts}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Categories</Typography>
                    <Typography sx={{ fontWeight: 'bold' }}>{counts.categories}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Transactions</Typography>
                    <Typography sx={{ fontWeight: 'bold', color: '#3b82f6' }}>{counts.transactions.toLocaleString()}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Portfolios</Typography>
                    <Typography sx={{ fontWeight: 'bold' }}>{counts.portfolios}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Stock Transactions</Typography>
                    <Typography sx={{ fontWeight: 'bold' }}>{counts.portfolio_transactions}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, pb: 1, borderBottom: '1px solid #e5e7eb' }}>
                    <Typography color="text.secondary">Market Prices</Typography>
                    <Typography sx={{ fontWeight: 'bold' }}>{counts.market_prices}</Typography>
                  </Box>
                  
                  {/* Total User Data */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', bgcolor: '#eff6ff', p: 2, borderRadius: 1, mb: 2 }}>
                    <Typography sx={{ fontWeight: 'bold' }}>Total User Data</Typography>
                    <Typography sx={{ fontWeight: 'bold', color: '#3b82f6', fontSize: '1.25rem' }}>{userDataCount.toLocaleString()}</Typography>
                  </Box>
                  
                  {/* Profile Section - Shown separately */}
                  <Typography variant="caption" sx={{ color: '#9ca3af', display: 'block', mt: 1 }}>
                    + Profile Settings (always present)
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Paper>
        </Grid>

        {/* Action Cards - Export, Import, Clear */}
        <Grid item xs={12} md={6}>
          <Grid container spacing={2} direction="column">
            {/* Export Card */}
            <Grid item>
              <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  color: 'white',
                  px: 2,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <Box sx={{ fontSize: 18 }}>📤</Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Export Data
                  </Typography>
                </Box>
                <CardContent sx={{ py: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Download all your data (profile, transactions, portfolios, categories) as a JSON backup file. 
                    Filename: <Typography component="span" sx={{ color: '#3b82f6' }}>Capricorn_UserData_YYYY-MM-DD_HHMM.json</Typography>
                  </Typography>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={isExporting ? <CircularProgress size={18} color="inherit" /> : <DownloadIcon />}
                    onClick={handleExport}
                    disabled={isExporting}
                    sx={{ 
                      bgcolor: '#10b981',
                      '&:hover': { bgcolor: '#059669' },
                      py: 1
                    }}
                  >
                    {isExporting ? 'Exporting...' : `Export All Data (${userDataCount.toLocaleString()} records + profile)`}
                  </Button>
                </CardContent>
              </Paper>
            </Grid>

            {/* Import Card - Compact */}
            <Grid item>
              <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                  color: 'white',
                  px: 2,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <Box sx={{ fontSize: 18 }}>📥</Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Import Data
                  </Typography>
                </Box>
                <CardContent sx={{ py: 2 }}>
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'flex-start', 
                    gap: 1, 
                    mb: 2, 
                    p: 1.5, 
                    bgcolor: '#fef3c7', 
                    borderRadius: 1,
                    border: '1px solid #fcd34d'
                  }}>
                    <WarningIcon sx={{ color: '#d97706', fontSize: 20, mt: 0.25 }} />
                    <Typography variant="body2" sx={{ color: '#92400e' }}>
                      <strong>Warning:</strong> Importing will <strong>REPLACE ALL</strong> existing data with the contents of the import file.
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Select a Capricorn backup file (<Typography component="span" sx={{ color: '#d97706' }}>Capricorn_UserData_*.json</Typography>) from your computer to restore.
                  </Typography>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept=".json"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={isImporting ? <CircularProgress size={18} color="inherit" /> : <UploadIcon />}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isImporting}
                    sx={{ 
                      bgcolor: '#f59e0b',
                      '&:hover': { bgcolor: '#d97706' },
                      py: 1
                    }}
                  >
                    {isImporting ? 'Importing...' : 'Select Backup File to Import'}
                  </Button>
                </CardContent>
              </Paper>
            </Grid>

            {/* Clear All Data Card */}
            <Grid item>
              <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                  color: 'white',
                  px: 2,
                  py: 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <Box sx={{ fontSize: 18 }}>🗑️</Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Clear All Data
                  </Typography>
                </Box>
                <CardContent sx={{ py: 2 }}>
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'flex-start', 
                    gap: 1, 
                    mb: 2, 
                    p: 1.5, 
                    bgcolor: '#fef2f2', 
                    borderRadius: 1,
                    border: '1px solid #fecaca'
                  }}>
                    <WarningIcon sx={{ color: '#dc2626', fontSize: 20, mt: 0.25 }} />
                    <Typography variant="body2" sx={{ color: '#991b1b' }}>
                      <strong>Warning:</strong> This will permanently delete ALL user data from the database. 
                      Export your data first before clearing!
                    </Typography>
                  </Box>
                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={isClearing ? <CircularProgress size={18} color="inherit" /> : <WarningIcon />}
                    onClick={() => setShowClearDialog(true)}
                    disabled={isClearing || userDataCount === 0}
                    sx={{ 
                      bgcolor: '#ef4444',
                      '&:hover': { bgcolor: '#dc2626' },
                      py: 1
                    }}
                  >
                    {isClearing ? 'Clearing...' : `Clear All User Data (${userDataCount.toLocaleString()} records)`}
                  </Button>
                </CardContent>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Footer Tip */}
      <Paper sx={{ mt: 3, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Export your data regularly as a backup. The export file can be imported on any Capricorn instance to restore your data after a fresh installation or to migrate to a new machine.
        </Typography>
      </Paper>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmDialog} onClose={handleImportCancel}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon sx={{ color: '#f59e0b' }} />
          Confirm Import
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will <strong>DELETE ALL</strong> existing data and replace it with the contents of:
          </DialogContentText>
          <Box sx={{ mt: 2, p: 2, bgcolor: '#f3f4f6', borderRadius: 1 }}>
            <Typography sx={{ fontWeight: 'bold' }}>{importFile?.name}</Typography>
          </Box>
          <DialogContentText sx={{ mt: 2 }}>
            Current data will be permanently deleted:
          </DialogContentText>
          <Box component="ul" sx={{ mt: 1 }}>
            <li>{counts.user_profile} User Profile</li>
            <li>{counts.transactions.toLocaleString()} Transactions</li>
            <li>{counts.portfolios} Portfolios</li>
            <li>{counts.portfolio_transactions} Stock Transactions</li>
          </Box>
          <DialogContentText sx={{ mt: 2, color: '#dc2626', fontWeight: 'bold' }}>
            This action cannot be undone!
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleImportCancel} variant="outlined">
            Cancel
          </Button>
          <Button 
            onClick={handleImportConfirm} 
            variant="contained" 
            color="warning"
            startIcon={<UploadIcon />}
          >
            Import & Replace All
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clear Data Confirmation Dialog */}
      <Dialog open={showClearDialog} onClose={() => setShowClearDialog(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#dc2626' }}>
          <WarningIcon sx={{ color: '#dc2626' }} />
          ⚠️ Clear All Data
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: '#991b1b', fontWeight: 'bold', mb: 2 }}>
            Are you sure you want to delete ALL user data from the database?
          </DialogContentText>
          <Box sx={{ p: 2, bgcolor: '#fef2f2', borderRadius: 1, border: '1px solid #fecaca', mb: 2 }}>
            <Typography sx={{ color: '#991b1b', mb: 1 }}>
              This will permanently delete:
            </Typography>
            <Box component="ul" sx={{ m: 0, pl: 2, color: '#991b1b' }}>
              <li>{counts.user_profile} User Profile</li>
              <li>{counts.accounts} Accounts</li>
              <li>{counts.categories} Categories</li>
              <li><strong>{counts.transactions.toLocaleString()} Transactions</strong></li>
              <li>{counts.portfolios} Portfolios</li>
              <li>{counts.portfolio_transactions} Stock Transactions</li>
              <li>{counts.market_prices} Market Prices</li>
            </Box>
          </Box>
          <DialogContentText sx={{ color: '#dc2626', fontWeight: 'bold' }}>
            🚨 THIS ACTION CANNOT BE UNDONE!
          </DialogContentText>
          <DialogContentText sx={{ mt: 1 }}>
            Make sure you have exported your data before proceeding.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setShowClearDialog(false)} variant="outlined">
            Cancel
          </Button>
          <Button 
            onClick={handleClearData} 
            variant="contained" 
            color="error"
            startIcon={<WarningIcon />}
          >
            Yes, Delete All Data
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

