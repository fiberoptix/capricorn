import axios from 'axios';
import { API_BASE_URL } from './config';

// API configuration now uses dynamic environment detection

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
export const financeAPI = {
  // Test connection to backend
  testConnection: async () => {
    const response = await axios.get(`${API_BASE_URL}/transactions`);
    return response;
  },

  // Get financial summary with optional time period filtering
  getFinancialSummary: async (options?: {
    period?: string;
    startDate?: string;
    endDate?: string;
  }) => {
    const params = new URLSearchParams();
    
    if (options?.period) {
      params.append('period', options.period);
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }

    const queryString = params.toString();
    const url = `${API_BASE_URL}/dashboard${queryString ? `?${queryString}` : ''}`;
    
    const response = await axios.get(url);
    return response;
  },

  // Get cumulative spending data by category over time
  getCumulativeSpending: async (options?: {
    period?: string;
    startDate?: string;
    endDate?: string;
  }) => {
    const params = new URLSearchParams();
    
    if (options?.period) {
      params.append('period', options.period);
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }

    const queryString = params.toString();
    const url = `${API_BASE_URL}/cumulative-spending${queryString ? `?${queryString}` : ''}`;
    
    const response = await axios.get(url);
    return response;
  },

  // Get transactions with optional time period filtering
  getTransactions: async (options?: {
    period?: string;
    startDate?: string;
    endDate?: string;
    skip?: number;
    limit?: number;
  }) => {
    const params = new URLSearchParams();
    
    if (options?.period) {
      params.append('period', options.period);
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }
    if (options?.skip !== undefined) {
      params.append('skip', options.skip.toString());
    }
    if (options?.limit !== undefined) {
      params.append('limit', options.limit.toString());
    }

    const queryString = params.toString();
    const url = `${API_BASE_URL}/transactions${queryString ? `?${queryString}` : ''}`;
    
    const response = await axios.get(url);
    return response;
  },

  // Get transaction summary with optional time period filtering
  getTransactionSummary: async (options?: {
    period?: string;
    startDate?: string;
    endDate?: string;
  }) => {
    const params = new URLSearchParams();
    
    if (options?.period) {
      params.append('period', options.period);
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }

    const queryString = params.toString();
    const url = `${API_BASE_URL}/transactions${queryString ? `?${queryString}` : ''}`;
    
    const response = await axios.get(url);
    return response;
  },

  // Upload multiple files (process each file)
  uploadMultipleFiles: async (formData: FormData) => {
    // Our new endpoint processes one file at a time
    // We'll need to handle multiple files by making multiple calls
    const response = await axios.post(`${API_BASE_URL}/process/upload-and-process`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response;
  },

  // Process files with steps (returns process ID)
  processFilesWithSteps: async () => {
    const response = await axios.post(`${API_BASE_URL}/process/process-steps`);
    return response;
  },

  // Get processing status
  getProcessingStatus: async (processId: string) => {
    const response = await axios.get(`${API_BASE_URL}/process/process-status/${processId}`);
    return response;
  },

  // Get data summary
  getDataSummary: async () => {
    const response = await axios.get(`${API_BASE_URL}/settings/data-summary/`);
    return response;
  },

  // Get transaction date ranges by account
  getTransactionDateRanges: async () => {
    const response = await axios.get(`${API_BASE_URL}/settings/transaction-date-ranges/`);
    return response;
  },

  // Get budget analysis data
  getBudgetAnalysis: async () => {
    const response = await axios.get(`${API_BASE_URL}/budget/category-analysis`);
    return response;
  },

  // Update transaction category
  updateTransactionCategory: async (transactionId: string, categoryId: string) => {
    const response = await axios.put(`${API_BASE_URL}/transactions/${transactionId}/category?category_id=${categoryId}`);
    return response;
  },

  // Get all categories
  getCategories: async () => {
    const response = await axios.get(`${API_BASE_URL}/categories`);
    return response;
  },

  // Tag Management
  // Get tags summary
  getTagsSummary: async () => {
    const response = await axios.get(`${API_BASE_URL}/settings/tags-summary/`);
    return response;
  },

  // Edit tag name
  editTag: async (tagName: string, newTagName: string) => {
    const response = await axios.put(`${API_BASE_URL}/settings/tags/${encodeURIComponent(tagName)}/edit`, {
      new_tag_name: newTagName
    });
    return response;
  },

  // Remove tag
  removeTag: async (tagName: string) => {
    const response = await axios.delete(`${API_BASE_URL}/settings/tags/${encodeURIComponent(tagName)}/remove`);
    return response;
  },

  // Migrate tag
  migrateTag: async (sourceTagName: string, targetTagName: string) => {
    const response = await axios.put(`${API_BASE_URL}/settings/tags/${encodeURIComponent(sourceTagName)}/migrate`, {
      target_tag_name: targetTagName
    });
    return response;
  },

  // Create new tag
  createTag: async (tagName: string) => {
    const response = await axios.post(`${API_BASE_URL}/settings/tags/create`, {
      new_tag_name: tagName
    });
    return response;
  },

  // Note: Export/Import/Clear functionality moved to DATA tab (Phase 10)
  // Uses /api/v1/data/* endpoints instead of /api/v1/banking/settings/*

  // Get double charges
  getDoubleCharges: async () => {
    const response = await axios.get(`${API_BASE_URL}/transactions/double-charges`);
    return response;
  },

  // Delete transaction
  deleteTransaction: async (transactionId: string) => {
    const response = await axios.delete(`${API_BASE_URL}/transactions/${transactionId}`);
    return response;
  },
};

export default api; 