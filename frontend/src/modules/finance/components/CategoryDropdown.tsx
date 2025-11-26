import React, { useState, useEffect } from 'react';
import {
  Menu,
  MenuItem,
  ListItemText,
  Chip,
  CircularProgress,
  Box,
  Typography,
  Alert,
  TextField,
  InputAdornment,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { financeAPI } from '../services/api';

interface Category {
  id: string;
  name: string;
}

interface CategoryDropdownProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
  onCategorySelect: (categoryId: string, categoryName: string) => void;
  currentCategory?: string;
  transactionId: string;
}

const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  anchorEl,
  open,
  onClose,
  onCategorySelect,
  currentCategory,
  transactionId
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  // Fetch categories when dropdown opens
  useEffect(() => {
    if (open && categories.length === 0) {
      fetchCategories();
    }
    // Reset search text when dropdown closes
    if (!open) {
      setSearchText('');
    }
    // Focus search input when menu opens
    if (open) {
      // Small delay to ensure the menu is rendered
      setTimeout(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      }, 100);
    }
  }, [open]);

  // Filter categories based on search text
  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchText.toLowerCase())
  );

  // Debug logging
  React.useEffect(() => {
    if (searchText) {
      console.log(`Searching for: "${searchText}", Found: ${filteredCategories.length} categories`);
    }
  }, [searchText, filteredCategories.length]);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await financeAPI.getCategories();
      
      if (response.data && response.data.success) {
        setCategories(response.data.data);
      } else {
        throw new Error(response.data?.message || 'Failed to fetch categories');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch categories');
      console.error('Category fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (category: Category) => {
    onCategorySelect(category.id, category.name);
    setSearchText(''); // Clear search text when a category is selected
    onClose();
  };

  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      disableAutoFocus={true}
      disableEnforceFocus={true}
      disableRestoreFocus={true}
      PaperProps={{
        style: {
          maxHeight: 380,
          width: '300px',
        },
      }}
      transformOrigin={{ horizontal: 'left', vertical: 'top' }}
      anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
      onKeyDown={(e) => {
        // Prevent menu from handling keyboard navigation
        e.stopPropagation();
      }}
    >
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}
      
      {error && (
        <Box sx={{ p: 2 }}>
          <Alert severity="error" sx={{ fontSize: '0.875rem' }}>
            {error}
          </Alert>
        </Box>
      )}
      
      {!loading && !error && (
        <>
          <Box sx={{ px: 2, py: 1, borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="body2" color="text.secondary" fontWeight={600}>
              Select Category
              {searchText && (
                <span style={{ marginLeft: '8px', fontWeight: 400 }}>
                  ({filteredCategories.length} found)
                </span>
              )}
            </Typography>
          </Box>
          
          {/* Search Field */}
          <Box sx={{ px: 2, py: 1, borderBottom: '1px solid #e0e0e0' }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search categories..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              inputRef={searchInputRef}
              onKeyDown={(e) => {
                // Prevent menu from closing on Enter
                if (e.key === 'Enter') {
                  e.preventDefault();
                  e.stopPropagation();
                }
                // Prevent menu from handling other keys
                e.stopPropagation();
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search sx={{ fontSize: 18, color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: 'rgba(46, 125, 50, 0.2)',
                  },
                  '&:hover fieldset': {
                    borderColor: 'rgba(46, 125, 50, 0.4)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#2e7d32',
                  },
                },
              }}
            />
          </Box>
          
          {filteredCategories.map((category) => (
            <MenuItem
              key={category.id}
              onClick={() => handleCategoryClick(category)}
              sx={{
                py: 1,
                px: 2,
                '&:hover': {
                  backgroundColor: 'rgba(46, 125, 50, 0.08)',
                },
                backgroundColor: currentCategory === category.name ? 'rgba(46, 125, 50, 0.12)' : 'transparent',
              }}
            >
              <ListItemText>
                <Chip
                  label={category.name}
                  size="small"
                  sx={{
                    backgroundColor: currentCategory === category.name ? '#2e7d32' : '#f5f5f5',
                    color: currentCategory === category.name ? 'white' : '#333',
                    fontWeight: currentCategory === category.name ? 600 : 500,
                    '&:hover': {
                      backgroundColor: currentCategory === category.name ? '#1b5e20' : '#e0e0e0',
                    },
                  }}
                />
              </ListItemText>
            </MenuItem>
          ))}
          
          {filteredCategories.length === 0 && categories.length > 0 && (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No categories match "{searchText}"
              </Typography>
            </Box>
          )}
          
          {categories.length === 0 && !loading && (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No categories available
              </Typography>
            </Box>
          )}
        </>
      )}
    </Menu>
  );
};

export default CategoryDropdown; 