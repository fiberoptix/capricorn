import React, { useState } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Box,
  Typography,
} from '@mui/material';
import { Search } from '@mui/icons-material';

interface CategorySelectorProps {
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  categories: string[];
  label?: string;
}

const CategorySelector: React.FC<CategorySelectorProps> = ({
  selectedCategory,
  onCategoryChange,
  categories,
  label = "Select Category"
}) => {
  const [searchText, setSearchText] = useState('');

  // Filter categories based on search text
  const filteredCategories = categories.filter(category =>
    category.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <Box sx={{ minWidth: 200 }}>
      <FormControl fullWidth variant="outlined">
        <InputLabel>{label}</InputLabel>
        <Select
          value={selectedCategory}
          onChange={(e) => onCategoryChange(e.target.value)}
          label={label}
        >
          {/* Search box */}
          <Box sx={{ px: 2, py: 1 }}>
            <TextField
              size="small"
              placeholder="Search categories..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search fontSize="small" />
                  </InputAdornment>
                ),
              }}
              onClick={(e) => e.stopPropagation()}
              fullWidth
            />
          </Box>
          
          {/* Categories list */}
          {filteredCategories.length > 0 ? (
            filteredCategories.map((category) => (
              <MenuItem key={category} value={category}>
                {category}
              </MenuItem>
            ))
          ) : (
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                No categories found
              </Typography>
            </MenuItem>
          )}
        </Select>
      </FormControl>
    </Box>
  );
};

export default CategorySelector; 