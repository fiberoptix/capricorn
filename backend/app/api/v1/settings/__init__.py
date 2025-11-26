"""
Settings API - App-wide settings that sync across all clients
"""
from fastapi import APIRouter

router = APIRouter(prefix="/settings", tags=["settings"])

from . import endpoints  # noqa

