import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
  CircularProgress,
  Snackbar,
  Chip,
} from '@mui/material';
import {
  Edit,
  Delete,
  SwapHoriz,
  Add,
  Close,
  Tag,
} from '@mui/icons-material';
import { financeAPI } from '../services/api';
import CategorySelector from './CategorySelector';

interface TagSummary {
  tag_name: string;
  record_count: number;
}

interface TagsSummaryData {
  tags: TagSummary[];
  total_tags: number;
}

const TagsSummary: React.FC = () => {
  const [tagsData, setTagsData] = useState<TagsSummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [migrateDialogOpen, setMigrateDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  
  // Current tag being edited/migrated/removed
  const [currentTag, setCurrentTag] = useState<string>('');
  const [newTagName, setNewTagName] = useState<string>('');
  const [targetTagName, setTargetTagName] = useState<string>('');
  
  // Available categories for migration
  const [categories, setCategories] = useState<string[]>([]);
  
  // Operation loading states
  const [isEditing, setIsEditing] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [isMigrating, setIsMigrating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    fetchTagsData();
    fetchCategories();
  }, []);

  const fetchTagsData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await financeAPI.getTagsSummary();
      if (response.data.success) {
        setTagsData(response.data.data);
      }
    } catch (err: any) {
      setError('Failed to fetch tags data');
      console.error('Error fetching tags data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await financeAPI.getCategories();
      if (response.data.success) {
        setCategories(response.data.data);
      }
    } catch (err: any) {
      console.error('Error fetching categories:', err);
    }
  };

  const handleEdit = (tagName: string) => {
    setCurrentTag(tagName);
    setNewTagName(tagName);
    setEditDialogOpen(true);
  };

  const handleMigrate = (tagName: string) => {
    setCurrentTag(tagName);
    setTargetTagName('');
    setMigrateDialogOpen(true);
  };

  const handleRemove = (tagName: string) => {
    setCurrentTag(tagName);
    setRemoveDialogOpen(true);
  };

  const handleCreateTag = () => {
    setNewTagName('');
    setCreateDialogOpen(true);
  };

  const performEdit = async () => {
    if (!newTagName.trim()) {
      setError('Category name cannot be empty');
      return;
    }

    try {
      setIsEditing(true);
      setError(null);
      const response = await financeAPI.editTag(currentTag, newTagName.trim());
      if (response.data.success) {
        setSuccessMessage(response.data.message);
        setEditDialogOpen(false);
        await fetchTagsData();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to edit category');
    } finally {
      setIsEditing(false);
    }
  };

  const performMigrate = async () => {
    if (!targetTagName.trim()) {
      setError('Please select a target category');
      return;
    }

    try {
      setIsMigrating(true);
      setError(null);
      const response = await financeAPI.migrateTag(currentTag, targetTagName);
      if (response.data.success) {
        setSuccessMessage(response.data.message);
        setMigrateDialogOpen(false);
        await fetchTagsData();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to migrate category');
    } finally {
      setIsMigrating(false);
    }
  };

  const performRemove = async () => {
    try {
      setIsRemoving(true);
      setError(null);
      const response = await financeAPI.removeTag(currentTag);
      if (response.data.success) {
        setSuccessMessage(response.data.message);
        setRemoveDialogOpen(false);
        await fetchTagsData();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove category');
    } finally {
      setIsRemoving(false);
    }
  };

  const performCreate = async () => {
    if (!newTagName.trim()) {
      setError('Category name cannot be empty');
      return;
    }

    try {
      setIsCreating(true);
      setError(null);
      const response = await financeAPI.createTag(newTagName.trim());
      if (response.data.success) {
        setSuccessMessage(response.data.message);
        setCreateDialogOpen(false);
        await fetchTagsData();
        await fetchCategories(); // Refresh categories list
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create category');
    } finally {
      setIsCreating(false);
    }
  };

  const closeDialogs = () => {
    setEditDialogOpen(false);
    setMigrateDialogOpen(false);
    setCreateDialogOpen(false);
    setRemoveDialogOpen(false);
    setCurrentTag('');
    setNewTagName('');
    setTargetTagName('');
  };

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Category Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage your transaction categories and their assignments
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleCreateTag}
          sx={{ mb: 1 }}
        >
          New Category
        </Button>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : tagsData && tagsData.tags.length > 0 ? (
        <TableContainer>
          <Table size="small" sx={{ '& .MuiTableCell-root': { py: 0.5 } }}>
            <TableHead>
              <TableRow>
                <TableCell>Category Name</TableCell>
                <TableCell align="right">Record Count</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tagsData.tags.map((tag) => (
                <TableRow key={tag.tag_name}>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Tag fontSize="small" color="primary" />
                      <Typography variant="body2">
                        {tag.tag_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={tag.record_count}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Box display="flex" gap={0.5} justifyContent="flex-end">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(tag.tag_name)}
                        title="Edit category name"
                        sx={{ p: 0.5 }}
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleMigrate(tag.tag_name)}
                        title="Migrate to another category"
                        sx={{ p: 0.5 }}
                      >
                        <SwapHoriz fontSize="small" />
                      </IconButton>
                      {tag.tag_name !== 'Uncategorized' && (
                        <IconButton
                          size="small"
                          onClick={() => handleRemove(tag.tag_name)}
                          title="Remove category"
                          color="error"
                          sx={{ p: 0.5 }}
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
          No tags found
        </Typography>
      )}

      {tagsData && (
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Total Categories: {tagsData.total_tags}
          </Typography>
        </Box>
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={closeDialogs} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Category</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Category Name"
            fullWidth
            variant="outlined"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialogs} disabled={isEditing}>
            Cancel
          </Button>
          <Button
            onClick={performEdit}
            variant="contained"
            disabled={isEditing}
          >
            {isEditing ? <CircularProgress size={20} /> : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Migrate Dialog */}
      <Dialog open={migrateDialogOpen} onClose={closeDialogs} maxWidth="sm" fullWidth>
        <DialogTitle>Migrate Category</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            All records with category "{currentTag}" will be moved to the selected target category.
          </Typography>
          <CategorySelector
            selectedCategory={targetTagName}
            onCategoryChange={(category: string) => setTargetTagName(category)}
            categories={categories}
            label="Target Category"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialogs} disabled={isMigrating}>
            Cancel
          </Button>
          <Button
            onClick={performMigrate}
            variant="contained"
            disabled={isMigrating}
          >
            {isMigrating ? <CircularProgress size={20} /> : 'Migrate'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Remove Dialog */}
      <Dialog open={removeDialogOpen} onClose={closeDialogs} maxWidth="sm" fullWidth>
        <DialogTitle>Remove Category</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Are you sure you want to remove the category "{currentTag}"?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            All records with this category will be changed to "Uncategorized".
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialogs} disabled={isRemoving}>
            Cancel
          </Button>
          <Button
            onClick={performRemove}
            variant="contained"
            color="error"
            disabled={isRemoving}
          >
            {isRemoving ? <CircularProgress size={20} /> : 'Remove'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={closeDialogs} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Category</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Category Name"
            fullWidth
            variant="outlined"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialogs} disabled={isCreating}>
            Cancel
          </Button>
          <Button
            onClick={performCreate}
            variant="contained"
            disabled={isCreating}
          >
            {isCreating ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={() => setSuccessMessage(null)}
      >
        <Alert onClose={() => setSuccessMessage(null)} severity="success">
          {successMessage}
        </Alert>
      </Snackbar>

      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          sx={{ mt: 2 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
    </Paper>
  );
};

export default TagsSummary; 