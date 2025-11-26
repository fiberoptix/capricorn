"""
Transaction Uploader Service - Stub for API endpoints
The actual uploader is in app.services.banking.uploader
This is a compatibility layer for the API endpoints
"""

from typing import Dict, Any
from fastapi import UploadFile
import asyncio

# Import the actual uploader from banking services
from app.services.banking.uploader import TransactionUploader as BankingUploader

# Create a global instance
uploader = BankingUploader()

# Add async wrappers for API compatibility
async def upload_file(file: UploadFile, user_id: str) -> Dict[str, Any]:
    """Async wrapper for file upload"""
    # For now, just return success
    # In production, this would save the file and trigger processing
    return {
        "file_id": "test-123",
        "filename": file.filename,
        "status": "uploaded",
        "user_id": user_id
    }

async def process_file(file_id: str, user_id: str) -> Dict[str, Any]:
    """Async wrapper for file processing"""
    # For now, just return success
    # In production, this would trigger the classification → parsing → tagging pipeline
    return {
        "file_id": file_id,
        "status": "processing",
        "message": "File processing started"
    }
