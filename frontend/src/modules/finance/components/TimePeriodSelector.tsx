import React, { useState } from 'react';
import { Box, Button, Modal, TextField, Typography, CircularProgress } from '@mui/material';

interface TimePeriodSelectorProps {
  onPeriodChange: (period: string, startDate?: string, endDate?: string) => void;
  currentPeriod: string;
  onFixUntagged?: () => void;
  showFixUntagged?: boolean;
  onDoubleCharges?: () => void;
  showDoubleCharges?: boolean;
  isLoadingDoubleCharges?: boolean;
}

const TimePeriodSelector: React.FC<TimePeriodSelectorProps> = ({ 
  onPeriodChange, 
  currentPeriod,
  onFixUntagged,
  showFixUntagged = false,
  onDoubleCharges,
  showDoubleCharges = false,
  isLoadingDoubleCharges = false
}) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showDateModal, setShowDateModal] = useState(false);

  const periodButtons = [
    { value: 'this_month', label: 'This Month' },
    { value: 'last_month', label: 'Last Month' },
    { value: 'last_3_months', label: '3 Months' },
    { value: 'this_year', label: 'This Year' },
    { value: 'all_time', label: 'All Time' },
    { value: 'date_range', label: 'Date Range' }
  ];

  const handlePeriodClick = (period: string) => {
    if (period === 'date_range') {
      setShowDateModal(true);
    } else {
      onPeriodChange(period);
    }
  };

  const handleDateRangeSubmit = () => {
    if (startDate && endDate) {
      onPeriodChange('date_range', startDate, endDate);
      setShowDateModal(false);
    }
  };

  const handleDateRangeCancel = () => {
    setShowDateModal(false);
    setStartDate('');
    setEndDate('');
  };

  return (
    <Box sx={{ 
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '20px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      border: '1px solid #e0e0e0'
    }}>
      <Box sx={{ 
        display: 'flex', 
        gap: 2, 
        flexWrap: 'wrap',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        {periodButtons.map((button) => (
          <Button
            key={button.value}
            onClick={() => handlePeriodClick(button.value)}
            variant={currentPeriod === button.value ? 'contained' : 'outlined'}
            sx={{
              background: currentPeriod === button.value 
                ? 'linear-gradient(135deg, #2e7d32 0%, #388e3c 100%)'
                : 'white',
              color: currentPeriod === button.value ? 'white' : '#2e7d32',
              borderColor: '#2e7d32',
              borderRadius: '20px',
              padding: '8px 16px',
              fontWeight: 600,
              fontSize: '0.875rem',
              textTransform: 'none',
              minWidth: 'auto',
              boxShadow: currentPeriod === button.value 
                ? '0 4px 15px rgba(46, 125, 50, 0.3)'
                : '0 2px 8px rgba(46, 125, 50, 0.1)',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: currentPeriod === button.value 
                  ? '0 6px 20px rgba(46, 125, 50, 0.4)'
                  : '0 4px 12px rgba(46, 125, 50, 0.2)',
                background: currentPeriod === button.value 
                  ? 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)'
                  : 'rgba(46, 125, 50, 0.05)',
              },
              '&:active': {
                transform: 'translateY(0px)',
              }
            }}
          >
            {button.label}
          </Button>
        ))}
        
        {/* Fix Untagged Button */}
        {onFixUntagged && (
          <Button
            onClick={onFixUntagged}
            variant={showFixUntagged ? 'contained' : 'outlined'}
            sx={{
              background: showFixUntagged 
                ? 'linear-gradient(135deg, #f57c00 0%, #ff9800 100%)'
                : 'white',
              color: showFixUntagged ? 'white' : '#f57c00',
              borderColor: '#f57c00',
              borderRadius: '20px',
              padding: '8px 16px',
              fontWeight: 600,
              fontSize: '0.875rem',
              textTransform: 'none',
              minWidth: 'auto',
              boxShadow: showFixUntagged 
                ? '0 4px 15px rgba(245, 124, 0, 0.3)'
                : '0 2px 8px rgba(245, 124, 0, 0.1)',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: showFixUntagged 
                  ? '0 6px 20px rgba(245, 124, 0, 0.4)'
                  : '0 4px 12px rgba(245, 124, 0, 0.2)',
                background: showFixUntagged 
                  ? 'linear-gradient(135deg, #ff9800 0%, #ffa726 100%)'
                  : 'rgba(245, 124, 0, 0.05)',
              },
              '&:active': {
                transform: 'translateY(0px)',
              }
            }}
          >
            Fix Untagged
          </Button>
        )}

        {/* Double Charges Button */}
        {onDoubleCharges && (
          <Button
            onClick={onDoubleCharges}
            disabled={isLoadingDoubleCharges}
            variant={showDoubleCharges ? 'contained' : 'outlined'}
            sx={{
              background: showDoubleCharges 
                ? 'linear-gradient(135deg, #d32f2f 0%, #f44336 100%)'
                : 'white',
              color: showDoubleCharges ? 'white' : '#d32f2f',
              borderColor: '#d32f2f',
              borderRadius: '20px',
              padding: '8px 16px',
              fontWeight: 600,
              fontSize: '0.875rem',
              textTransform: 'none',
              minWidth: 'auto',
              boxShadow: showDoubleCharges 
                ? '0 4px 15px rgba(211, 47, 47, 0.3)'
                : '0 2px 8px rgba(211, 47, 47, 0.1)',
              transition: 'all 0.3s ease-in-out',
              '&:hover': {
                transform: isLoadingDoubleCharges ? 'none' : 'translateY(-2px)',
                boxShadow: showDoubleCharges 
                  ? '0 6px 20px rgba(211, 47, 47, 0.4)'
                  : '0 4px 12px rgba(211, 47, 47, 0.2)',
                background: showDoubleCharges 
                  ? 'linear-gradient(135deg, #f44336 0%, #e53935 100%)'
                  : 'rgba(211, 47, 47, 0.05)',
              },
              '&:active': {
                transform: 'translateY(0px)',
              },
              '&:disabled': {
                background: '#f5f5f5',
                color: '#999',
                borderColor: '#ddd',
                transform: 'none',
                boxShadow: 'none',
              }
            }}
          >
            {isLoadingDoubleCharges ? (
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={16} color="inherit" />
                <span>Searching...</span>
              </Box>
            ) : (
              'Double Charges'
            )}
          </Button>
        )}
      </Box>

      {/* Date Range Modal */}
      <Modal
        open={showDateModal}
        onClose={handleDateRangeCancel}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box sx={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '32px',
          minWidth: '400px',
          maxWidth: '90vw',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          outline: 'none',
        }}>
          <Typography variant="h6" gutterBottom sx={{ 
            fontWeight: 600, 
            color: '#2e7d32',
            textAlign: 'center',
            mb: 3
          }}>
            Select Date Range
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{
                shrink: true,
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: '#2e7d32',
                  },
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#2e7d32',
                },
              }}
            />
            
            <TextField
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{
                shrink: true,
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: '#2e7d32',
                  },
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#2e7d32',
                },
              }}
            />
          </Box>

          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'flex-end', 
            gap: 2, 
            mt: 4 
          }}>
            <Button
              onClick={handleDateRangeCancel}
              variant="outlined"
              sx={{
                color: '#666',
                borderColor: '#ddd',
                '&:hover': {
                  borderColor: '#999',
                  backgroundColor: '#f5f5f5',
                },
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleDateRangeSubmit}
              disabled={!startDate || !endDate}
              variant="contained"
              sx={{
                background: 'linear-gradient(135deg, #2e7d32 0%, #388e3c 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #388e3c 0%, #4caf50 100%)',
                },
                '&:disabled': {
                  background: '#ccc',
                  color: '#666',
                },
              }}
            >
              Apply
            </Button>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default TimePeriodSelector; 