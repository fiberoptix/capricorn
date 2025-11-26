/**
 * Upload Page - Standardized UI/UX
 * Upload and process banking CSV files
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
  IconButton,
  Collapse,
  Stack,
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Error,
  ExpandMore,
  ExpandLess,
  PlayArrow,
  Description,
  Category,
  Tag,
  Storage,
  FilterList,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { financeAPI } from '../services/api';

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  error?: string;
}

interface ProcessingStep {
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
  details?: any;
  icon: React.ReactNode;
}

const Upload: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadResults, setUploadResults] = useState<any>(null);
  const [processingResults, setProcessingResults] = useState<any>(null);
  const [expandedSteps, setExpandedSteps] = useState<{ [key: string]: boolean }>({});

  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    { name: 'Classification', status: 'pending', icon: <Category />, message: 'Classify files by bank type (BOFA/AMEX)' },
    { name: 'Parsing', status: 'pending', icon: <Description />, message: 'Parse transactions from CSV files' },
    { name: 'Auto-Tagging', status: 'pending', icon: <Tag />, message: 'Apply 97.1% accurate auto-tagging' },
    { name: 'Duplicate Detection', status: 'pending', icon: <FilterList />, message: 'Check for duplicate transactions' },
    { name: 'Database Save', status: 'pending', icon: <Storage />, message: 'Save transactions to database' },
  ]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.slice(0, 50 - files.length);
    const uploadFiles: UploadedFile[] = newFiles.map(file => ({ file, status: 'pending' as const }));
    setFiles(prev => [...prev, ...uploadFiles]);
  }, [files.length]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 50,
  });

  const clearFiles = () => {
    setFiles([]);
    setUploadResults(null);
    setProcessingResults(null);
    setProcessingSteps(steps => steps.map(step => ({ ...step, status: 'pending', details: undefined })));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const })));

    try {
      let successCount = 0;
      let failedCount = 0;
      
      for (const uploadFile of files) {
        const formData = new FormData();
        formData.append('file', uploadFile.file);
        
        let accountName = 'Bank of America Checking';
        const fileName = uploadFile.file.name.toUpperCase();
        if (fileName.includes('AMEX')) accountName = 'American Express';
        else if (fileName.includes('CREDIT')) accountName = 'Bank of America Credit';
        formData.append('account_name', accountName);
        
        try {
          const response = await financeAPI.uploadMultipleFiles(formData);
          if (response.data.status === 'success') {
            successCount++;
            setFiles(prev => prev.map(f => f.file.name === uploadFile.file.name ? { ...f, status: 'uploaded' as const } : f));
          } else {
            failedCount++;
            setFiles(prev => prev.map(f => f.file.name === uploadFile.file.name ? { ...f, status: 'error' as const, error: 'Upload failed' } : f));
          }
        } catch (err) {
          failedCount++;
          setFiles(prev => prev.map(f => f.file.name === uploadFile.file.name ? { ...f, status: 'error' as const, error: 'Upload failed' } : f));
        }
      }
      
      setUploadResults({
        ready_for_processing: successCount > 0,
        successful_uploads: successCount,
        failed_uploads_count: failedCount,
        total_files: files.length,
      });
    } catch (error: any) {
      setFiles(prev => prev.map(f => ({ ...f, status: 'error' as const, error: error.response?.data?.detail || 'Upload failed' })));
    } finally {
      setIsUploading(false);
    }
  };

  const processFiles = async () => {
    if (!uploadResults?.ready_for_processing) return;
    setIsProcessing(true);
    setProcessingSteps(steps => steps.map(step => ({ ...step, status: 'pending', details: undefined })));
    setExpandedSteps({});
    
    try {
      const response = await financeAPI.processFilesWithSteps();
      if (response.data.success) {
        const processId = response.data.process_id;
        
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await financeAPI.getProcessingStatus(processId);
            if (statusResponse.data.success) {
              const status = statusResponse.data.data;
              
              setProcessingSteps(prev => prev.map(step => {
                let stepKey = '';
                switch (step.name) {
                  case 'Classification': stepKey = 'classification'; break;
                  case 'Parsing': stepKey = 'parsing'; break;
                  case 'Auto-Tagging': stepKey = 'tagging'; break;
                  case 'Duplicate Detection': stepKey = 'duplicate_check'; break;
                  case 'Database Save': stepKey = 'database'; break;
                }
                
                if (stepKey && status.steps[stepKey]) {
                  const stepData = status.steps[stepKey];
                  if (stepData.status === 'processing' && step.status !== 'processing') {
                    setExpandedSteps(prev => ({ ...prev, [step.name]: true }));
                  }
                  return { ...step, status: stepData.status || 'pending', details: stepData, message: stepData.message || step.message };
                }
                return step;
              }));
              
              if (status.status === 'completed' || status.status === 'failed') {
                clearInterval(pollInterval);
                setIsProcessing(false);
                setProcessingResults(status);
                setExpandedSteps({ 'Classification': true, 'Parsing': true, 'Auto-Tagging': true, 'Duplicate Detection': true, 'Database Save': true });
              }
            }
          } catch (error) {
            console.error('Error polling status:', error);
          }
        }, 500);
        
        setTimeout(() => { clearInterval(pollInterval); setIsProcessing(false); }, 300000);
      }
    } catch (error: any) {
      setProcessingSteps(prev => prev.map(step => ({ ...step, status: 'failed', message: error.response?.data?.detail || 'Processing failed' })));
      setIsProcessing(false);
    }
  };

  const toggleStepExpanded = (stepName: string) => {
    setExpandedSteps(prev => ({ ...prev, [stepName]: !prev[stepName] }));
  };

  const getFileIcon = (status: string) => {
    switch (status) {
      case 'uploaded': return <CheckCircle color="success" />;
      case 'error': return <Error color="error" />;
      default: return <InsertDriveFile />;
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Main Header */}
      <Paper sx={{ 
        background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CloudUpload sx={{ fontSize: 40 }} />
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              Upload Banking Files
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Upload CSV files from Bank of America and American Express
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Upload Section */}
      <Paper sx={{ overflow: 'hidden', borderRadius: 2, mb: 3 }}>
        <Box sx={{ 
          background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
          color: 'white',
          px: 2,
          py: 1.5,
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <UploadIcon />
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            📁 File Upload
          </Typography>
        </Box>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'action.hover' : 'transparent',
              transition: 'all 0.3s',
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here' : 'Drag & drop CSV files here'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              or click to select files (max 50 files)
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Supported: Bank of America and American Express CSV files
            </Typography>
          </Box>

          {files.length > 0 && (
            <>
              <Box sx={{ mt: 3, mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">Selected Files ({files.length})</Typography>
                <Button onClick={clearFiles} size="small">Clear All</Button>
              </Box>
              
              <List dense sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'grey.50', borderRadius: 1 }}>
                {files.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>{getFileIcon(file.status)}</ListItemIcon>
                    <ListItemText primary={file.file.name} secondary={file.error || `${(file.file.size / 1024).toFixed(2)} KB`} />
                    {file.status === 'uploading' && <LinearProgress sx={{ width: 100 }} />}
                  </ListItem>
                ))}
              </List>

              <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                <Button variant="contained" onClick={uploadFiles} disabled={isUploading || files.some(f => f.status === 'uploaded')} startIcon={<CloudUpload />}>
                  Upload Files
                </Button>
                {uploadResults?.ready_for_processing && (
                  <Button variant="contained" color="success" onClick={processFiles} disabled={isProcessing} startIcon={<PlayArrow />}>
                    Process All Files
                  </Button>
                )}
              </Box>
            </>
          )}
        </CardContent>
      </Paper>

      {/* Upload Results */}
      {uploadResults && (
        <Alert severity={uploadResults.failed_uploads_count > 0 ? 'warning' : 'success'} sx={{ mb: 3 }}>
          Successfully uploaded {uploadResults.successful_uploads} of {uploadResults.total_files} files
        </Alert>
      )}

      {/* Processing Status Section */}
      {(uploadResults?.ready_for_processing || processingResults) && (
        <Paper sx={{ overflow: 'hidden', borderRadius: 2 }}>
          <Box sx={{ 
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: 'white',
            px: 2,
            py: 1.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            <PlayArrow />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              ⚙️ Processing Status
            </Typography>
          </Box>
          <CardContent>
            <Grid container spacing={2}>
              {processingSteps.map((step) => (
                <Grid item xs={12} key={step.name}>
                  <Card variant="outlined">
                    <CardContent sx={{ py: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          {step.icon}
                          <Box>
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>{step.name}</Typography>
                            <Typography variant="body2" color="text.secondary">{step.message}</Typography>
                          </Box>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip 
                            label={step.status} 
                            color={getStepColor(step.status) as any}
                            size="small"
                            sx={{ animation: step.status === 'processing' ? 'pulse 1.5s ease-in-out infinite' : 'none' }}
                          />
                          {step.details?.output?.length > 0 && (
                            <IconButton size="small" onClick={() => toggleStepExpanded(step.name)}>
                              {expandedSteps[step.name] ? <ExpandLess /> : <ExpandMore />}
                            </IconButton>
                          )}
                        </Box>
                      </Box>
                      
                      <Collapse in={expandedSteps[step.name] || step.status === 'processing'}>
                        {step.details && (
                          <Box sx={{ mt: 2 }}>
                            {(step.details.output?.length > 0 || step.status === 'processing') && (
                              <Box sx={{ bgcolor: '#1e1e1e', color: '#d4d4d4', p: 2, borderRadius: 1, fontFamily: 'monospace', fontSize: '0.875rem', maxHeight: 200, overflow: 'auto', mb: 2 }}>
                                {step.status === 'processing' && !step.details.output?.length ? (
                                  <div style={{ color: '#569cd6' }}>Processing... Output will appear here.</div>
                                ) : (
                                  step.details.output?.map((line: string, index: number) => (
                                    <div key={index} style={{ marginBottom: '2px' }}>{line}</div>
                                  ))
                                )}
                              </Box>
                            )}
                          </Box>
                        )}
                      </Collapse>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {processingResults?.statistics && (
              <Box sx={{ mt: 3 }}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="h6" gutterBottom>Processing Summary</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">Files Processed</Typography>
                    <Typography variant="h6">{processingResults.statistics.total_files_processed || 0}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">Transactions Found</Typography>
                    <Typography variant="h6">{processingResults.statistics.total_transactions || 0}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">Auto-Tagged</Typography>
                    <Typography variant="h6">{processingResults.statistics.transactions_tagged || 0}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">Tagging Accuracy</Typography>
                    <Typography variant="h6" color="success.main">{processingResults.statistics.tagging_accuracy || '0%'}</Typography>
                  </Grid>
                </Grid>
              </Box>
            )}
          </CardContent>
        </Paper>
      )}

      {/* Footer */}
      <Paper sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          <strong>💡 Tip:</strong> Upload CSV files downloaded from your bank's website. The system automatically detects the bank type and applies 97% accurate auto-tagging.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Upload;
