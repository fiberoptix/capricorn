import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Box, Typography, IconButton, Chip, Switch, Tooltip, CircularProgress, Alert, AlertTitle, Link } from '@mui/material';
import { Brightness4, Brightness7, TrendingUp, WarningAmber } from '@mui/icons-material';
import { useThemeMode } from '../theme/ThemeProvider';
import { useQueryClient } from '@tanstack/react-query';
import { API_V1_URL } from '../config/api';

// Constants for localStorage keys
const TWELVEDATA_BANNER_DISMISSED_KEY = 'capricorn_twelvedata_banner_dismissed_timestamp';

interface DockerStatus {
  total: number;
  running: number;
}

interface RefreshStatus {
  is_running: boolean;
  total_symbols: number;
  completed_symbols: number;
  minutes_remaining: number;
  progress_percent: number;
  status_message: string;
  error: string | null;
}

// Check if currently within market hours (9:30 AM - 4:15 PM EST, weekdays)
const isMarketHours = (): boolean => {
  const now = new Date();
  const estOptions: Intl.DateTimeFormatOptions = { timeZone: 'America/New_York', hour: 'numeric', minute: 'numeric', hour12: false };
  const estTime = new Intl.DateTimeFormat('en-US', estOptions).format(now);
  const [hours, minutes] = estTime.split(':').map(Number);
  const totalMinutes = hours * 60 + minutes;
  
  // Check weekday (0 = Sunday, 6 = Saturday)
  const estDay = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' })).getDay();
  if (estDay === 0 || estDay === 6) return false;
  
  // Market hours: 9:30 AM (570 min) to 4:15 PM (975 min)
  return totalMinutes >= 570 && totalMinutes <= 975;
};

export const Banner: React.FC = () => {
  const { mode, toggleTheme } = useThemeMode();
  const queryClient = useQueryClient();
  const [buildNumber, setBuildNumber] = useState<string>('DEV');
  const [dockerStatus, setDockerStatus] = useState<DockerStatus>({ total: 4, running: 4 });
  
  // Real-time pricing state (synced with backend database)
  const [realtimePricingEnabled, setRealtimePricingEnabled] = useState<boolean>(false);
  const [isLoadingSetting, setIsLoadingSetting] = useState(true);
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatus | null>(null);
  const [lastRefresh, setLastRefresh] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const statusPollRef = useRef<NodeJS.Timeout | null>(null);
  
  // TwelveData API key configuration state
  const [apiKeyConfigured, setApiKeyConfigured] = useState<boolean>(true); // Assume configured until we check
  const [showApiBanner, setShowApiBanner] = useState<boolean>(false);
  
  // GCP Demo Mode state
  const [isGcpMode, setIsGcpMode] = useState<boolean>(false);
  const [minutesRemaining, setMinutesRemaining] = useState<number | null>(null);
  const gcpCheckRef = useRef<NodeJS.Timeout | null>(null);

  // Check TwelveData API key status and show banner if needed
  useEffect(() => {
    const checkApiKeyStatus = async () => {
      try {
        const response = await fetch(`${API_V1_URL}/settings/twelvedata-status`);
        if (response.ok) {
          const data = await response.json();
          setApiKeyConfigured(data.is_configured);
          
          // Show banner if not configured AND (never dismissed OR 7 days passed)
          if (!data.is_configured) {
            const dismissedTimestamp = localStorage.getItem(TWELVEDATA_BANNER_DISMISSED_KEY);
            if (!dismissedTimestamp) {
              // Never dismissed - show banner
              setShowApiBanner(true);
            } else {
              // Check if 7 days have passed
              const daysSinceDismissal = (Date.now() - parseInt(dismissedTimestamp)) / (1000 * 60 * 60 * 24);
              if (daysSinceDismissal >= 7) {
                setShowApiBanner(true);
              }
            }
          }
        }
      } catch (error) {
        // Fail silently - assume configured if we can't check
        console.error('Failed to check TwelveData API status:', error);
      }
    };
    checkApiKeyStatus();
  }, []);

  // Handle dismissing the API key banner
  const handleDismissApiBanner = () => {
    localStorage.setItem(TWELVEDATA_BANNER_DISMISSED_KEY, Date.now().toString());
    setShowApiBanner(false);
  };

  // Fetch realtime pricing setting from backend on mount
  useEffect(() => {
    const fetchSetting = async () => {
      try {
        const response = await fetch(`${API_V1_URL}/settings/realtime-pricing`);
        if (response.ok) {
          const data = await response.json();
          setRealtimePricingEnabled(data.enabled);
          setIsGcpMode(data.is_gcp || false);
          setMinutesRemaining(data.minutes_remaining);
          
          // If GCP mode and enabled, start polling for countdown
          if (data.is_gcp && data.enabled) {
            startGcpCountdownPolling();
          }
        }
      } catch (error) {
        console.error('Failed to fetch realtime pricing setting:', error);
      } finally {
        setIsLoadingSetting(false);
      }
    };
    fetchSetting();
    
    // Also check if there's an active refresh
    checkRefreshStatus();
    
    // Cleanup GCP polling on unmount
    return () => {
      if (gcpCheckRef.current) {
        clearInterval(gcpCheckRef.current);
      }
    };
  }, []);
  
  // Function to check refresh status
  const checkRefreshStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh-status`);
      if (response.ok) {
        const data = await response.json();
        // Only set status if refresh is actively running
        // This prevents showing stale "completed" status on page load
        if (data.status?.is_running) {
          setRefreshStatus(data.status);
        }
        return data.status;
      }
    } catch (error) {
      console.error('Failed to check refresh status:', error);
    }
    return null;
  }, []);

  // Helper to stop polling and finalize refresh state
  const stopPollingAndFinalize = useCallback((completedSymbols: number = 0) => {
    if (statusPollRef.current) {
      clearInterval(statusPollRef.current);
      statusPollRef.current = null;
    }
    
    // Update last refresh time
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      timeZone: 'America/New_York'
    });
    setLastRefresh(timeStr);
    
    // Invalidate all portfolio-related queries to refresh UI
    queryClient.invalidateQueries({ queryKey: ['market-prices'] });
    queryClient.invalidateQueries({ queryKey: ['portfolios'] });
    queryClient.invalidateQueries({ queryKey: ['break-even'] });
    queryClient.invalidateQueries({ queryKey: ['portfolio-summary'] });
    
    console.log(`✅ Background refresh complete: ${completedSymbols} prices updated`);
    
    // Show "Done" message briefly, then clear
    setRefreshStatus({ is_running: false, status_message: `Done: ${completedSymbols} prices updated`, completed_symbols: completedSymbols });
    setTimeout(() => setRefreshStatus(null), 3000);
  }, [queryClient]);

  // Poll for status updates during background refresh
  const startStatusPolling = useCallback((totalBatches: number = 2) => {
    // Clear any existing poll
    if (statusPollRef.current) {
      clearInterval(statusPollRef.current);
    }
    
    // Calculate max timeout: 65 seconds per batch + 30 second buffer
    // Batch 1: immediate (~5s), Batch 2: 60s + 5s, Batch 3: 120s + 5s, etc.
    const maxTimeoutMs = (totalBatches * 65 + 30) * 1000;
    const startTime = Date.now();
    
    console.log(`⏱️ Starting status polling with ${maxTimeoutMs / 1000}s timeout for ${totalBatches} batches`);
    
    // Poll every 2 seconds
    statusPollRef.current = setInterval(async () => {
      try {
        // Check if we've exceeded max timeout - failsafe to stop spinner
        const elapsed = Date.now() - startTime;
        if (elapsed > maxTimeoutMs) {
          console.log(`⏰ Timeout reached (${elapsed / 1000}s > ${maxTimeoutMs / 1000}s), stopping spinner`);
          stopPollingAndFinalize(0);
          return;
        }
        
        const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh-status`);
        if (!response.ok) return;
        
        const data = await response.json();
        const status = data.status;
        
        if (!status) return;
        
        // Always update status while polling (to show progress)
        setRefreshStatus(status);
        
        if (!status.is_running) {
          // Refresh complete - stop polling
          stopPollingAndFinalize(status.completed_symbols || 0);
        }
      } catch (error) {
        console.error('Failed to check refresh status:', error);
      }
    }, 2000);
  }, [stopPollingAndFinalize]);

  // Function to start background market price refresh
  const refreshMarketPrices = useCallback(async (force: boolean = false) => {
    // Only auto-refresh during market hours (manual refresh always works)
    if (!force && !isMarketHours()) {
      console.log('⏰ Skipping auto-refresh: outside market hours');
      return;
    }
    
    try {
      // Set initial "Starting..." status
      setRefreshStatus({ is_running: true, status_message: 'Starting...', completed_symbols: 0 });
      
      // Start the background refresh
      const response = await fetch(`${API_V1_URL}/portfolio/market-prices/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: true }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`🚀 Background refresh started:`, data.status?.status_message);
        if (data.status) {
          setRefreshStatus(data.status);
        }
        
        // Start polling for status updates with batch count for timeout calculation
        const totalBatches = data.status?.total_batches || 2;
        startStatusPolling(totalBatches);
      } else {
        // Clear status on error
        setRefreshStatus(null);
      }
    } catch (error) {
      console.error('❌ Failed to start market price refresh:', error);
      setRefreshStatus(null);
    }
  }, [startStatusPolling]);
  
  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (statusPollRef.current) {
        clearInterval(statusPollRef.current);
      }
    };
  }, []);

  // GCP Demo Mode: Poll every minute to update countdown and auto-disable
  const startGcpCountdownPolling = useCallback(() => {
    // Clear any existing poll
    if (gcpCheckRef.current) {
      clearInterval(gcpCheckRef.current);
    }
    
    // Poll every minute
    gcpCheckRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_V1_URL}/settings/realtime-pricing`);
        if (response.ok) {
          const data = await response.json();
          setMinutesRemaining(data.minutes_remaining);
          
          // If backend auto-disabled, update UI
          if (!data.enabled && realtimePricingEnabled) {
            setRealtimePricingEnabled(false);
            console.log('⏱️ GCP Demo Mode: Live pricing auto-disabled after 20 minutes');
            // Stop polling
            if (gcpCheckRef.current) {
              clearInterval(gcpCheckRef.current);
              gcpCheckRef.current = null;
            }
          }
        }
      } catch (error) {
        console.error('Failed to check GCP countdown:', error);
      }
    }, 60000); // Every minute
  }, [realtimePricingEnabled]);

  // Handle toggle change - save to backend database
  const handleToggle = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.checked;
    setRealtimePricingEnabled(newValue);
    
    // Save to backend (syncs across all clients)
    try {
      const response = await fetch(`${API_V1_URL}/settings/realtime-pricing?enabled=${newValue}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log(`🔧 Realtime pricing ${newValue ? 'enabled' : 'disabled'} (saved to database)`);
        
        // Handle GCP mode
        if (data.is_gcp) {
          setIsGcpMode(true);
          if (newValue && data.timeout_minutes) {
            setMinutesRemaining(data.timeout_minutes);
            startGcpCountdownPolling();
          } else {
            setMinutesRemaining(null);
            if (gcpCheckRef.current) {
              clearInterval(gcpCheckRef.current);
              gcpCheckRef.current = null;
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to save realtime pricing setting:', error);
    }
    
    if (newValue) {
      // When turning ON, do an immediate refresh
      refreshMarketPrices(true);
    }
  }, [refreshMarketPrices, startGcpCountdownPolling]);

  // Set up interval when enabled
  useEffect(() => {
    if (realtimePricingEnabled) {
      // Refresh every 15 minutes (900000 ms)
      intervalRef.current = setInterval(() => {
        refreshMarketPrices(false); // Auto-refresh respects market hours
      }, 15 * 60 * 1000);
      
      console.log('🔄 Real-time pricing enabled: checking every 15 minutes');
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      console.log('⏸️ Real-time pricing disabled');
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [realtimePricingEnabled, refreshMarketPrices]);

  useEffect(() => {
    // Get build number from Vite env var (baked in at build time)
    const envBuildNumber = import.meta.env.VITE_BUILD_NUMBER;
    if (envBuildNumber) {
      setBuildNumber(envBuildNumber);
    }

    // Check Docker status
    fetch('/api/docker/status')
      .then(res => res.json())
      .then(data => {
        setDockerStatus({ total: data.total || 4, running: data.running || 4 });
      })
      .catch(() => {});
  }, []);

  const allContainersUp = dockerStatus.running === dockerStatus.total;

  return (
    <>
      {/* Dismissible banner when TwelveData API key not configured */}
      {showApiBanner && (
        <Alert 
          severity="warning"
          onClose={handleDismissApiBanner}
          sx={{ 
            borderRadius: 0, 
            mb: 0,
            '& .MuiAlert-message': { width: '100%' }
          }}
        >
          <AlertTitle sx={{ fontWeight: 'bold' }}>Live Stock Prices Disabled</AlertTitle>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="body2">
              TwelveData API key not configured. Portfolio values will use cost basis (purchase price).
            </Typography>
            <Link 
              href="https://github.com/fiberoptix/capricorn#twelvedata-api-optional---for-live-stock-prices" 
              target="_blank"
              sx={{ fontWeight: 'bold' }}
            >
              Configure API Key
            </Link>
            <Typography variant="body2">
              or enter prices manually in Portfolio → Market Prices.
            </Typography>
          </Box>
        </Alert>
      )}
      <Box
        sx={{
          height: '100px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 4,
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
      {/* Left: Logo & App Name */}
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Box
          component="img"
          src="/capricorn_icon.ico"
          alt="Capricorn"
          sx={{
            width: 96,
            height: 96,
            objectFit: 'contain',
            mr: 1,
            transform: 'scaleX(-1)',  // Flip horizontally
          }}
        />
        <Box sx={{ ml: '18px' }}>
          <Typography variant="h4" fontWeight="bold">
            Capricorn
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Unified Financial Platform
          </Typography>
        </Box>
      </Box>

      {/* Right: Real-Time Pricing, Build Number, Docker Status, Theme Toggle */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Real-Time Pricing Toggle with Status */}
        <Tooltip 
          title={
            realtimePricingEnabled 
              ? (isGcpMode && minutesRemaining !== null
                  ? `Demo mode: auto-disables in ${minutesRemaining} min${lastRefresh ? ` (Last: ${lastRefresh})` : ''}`
                  : `Auto-refreshing prices every 15 min during market hours${lastRefresh ? ` (Last: ${lastRefresh})` : ''}`)
              : (isGcpMode 
                  ? 'Demo mode: Live pricing resets after 20 minutes'
                  : 'Click to enable automatic price updates')
          }
        >
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              gap: 0.25,
            }}
          >
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 0.5,
                bgcolor: 'white',
                px: 1.5,
                py: 0.5,
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'grey.300',
              }}
            >
              {refreshStatus?.is_running ? (
                <CircularProgress size={16} sx={{ color: 'info.main' }} />
              ) : (
                <TrendingUp sx={{ fontSize: 18, color: realtimePricingEnabled ? 'success.main' : 'error.main' }} />
              )}
              <Typography 
                variant="caption" 
                sx={{ 
                  fontWeight: 'bold', 
                  color: realtimePricingEnabled ? 'success.main' : 'error.main',
                  whiteSpace: 'nowrap'
                }}
              >
                {realtimePricingEnabled 
                  ? (isGcpMode && minutesRemaining !== null 
                      ? `Live: ON (${minutesRemaining}m)` 
                      : 'Live Prices: ON')
                  : 'Live Prices: OFF'}
              </Typography>
              {/* Warning icon when API key not configured */}
              {!apiKeyConfigured && (
                <Tooltip title="TwelveData API key not configured. Prices will use cost basis.">
                  <WarningAmber sx={{ fontSize: 16, color: 'warning.main', ml: 0.5 }} />
                </Tooltip>
              )}
              <Switch
                checked={realtimePricingEnabled}
                onChange={handleToggle}
                size="small"
                disabled={refreshStatus?.is_running}
                sx={{ 
                  ml: 0.5,
                  '& .MuiSwitch-switchBase.Mui-checked': {
                    color: 'success.main',
                  },
                  '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                    backgroundColor: 'success.main',
                  },
                  '& .MuiSwitch-switchBase': {
                    color: 'error.main',
                  },
                  '& .MuiSwitch-track': {
                    backgroundColor: 'error.main',
                  },
                }}
              />
            </Box>
            {/* Status message when refreshing */}
            {refreshStatus && (refreshStatus.is_running || refreshStatus.completed_symbols > 0) && (
              <Typography 
                variant="caption" 
                sx={{ 
                  color: refreshStatus.is_running ? 'info.main' : 'success.main',
                  fontSize: '0.65rem',
                  whiteSpace: 'nowrap',
                  maxWidth: 180,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {refreshStatus.status_message}
              </Typography>
            )}
          </Box>
        </Tooltip>

        <Chip
          label={`Build ${buildNumber}`}
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label={`Docker ${dockerStatus.running}/${dockerStatus.total}`}
          size="small"
          color={allContainersUp ? 'success' : 'warning'}
        />
        <IconButton onClick={toggleTheme} color="inherit">
          {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
        </IconButton>
      </Box>
    </Box>
    </>
  );
};

