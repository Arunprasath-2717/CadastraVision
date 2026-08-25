"""
app/services/storage_service.py
──────────────────────────────────
Unified object storage abstraction layer for CadastraVision.

Provides provider-agnostic storage operations (Local Storage & S3/MinIO)
protecting against path traversal, exposing virtual URIs, and managing
lifecycle & cleanup.
"""

from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO
from fastapi import HTTPException, status


class BaseStorageProvider(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    async def save_object(self, key: str, data: bytes) -> str:
        """Save bytes payload to storage under given key and return storage URI."""
        pass

    @abstractmethod
    async def get_object(self, key: str) -> bytes:
        """Retrieve bytes payload for given key."""
        pass

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        """Delete object under given key."""
        pass

    @abstractmethod
    async def object_exists(self, key: str) -> bool:
        """Check if object exists under given key."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local filesystem storage provider with path-traversal safeguards.
    """

    def __init__(self, base_dir: str = "/tmp/cadastravision_storage"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_safe_path(self, key: str) -> str:
        clean_key = os.path.basename(key)
        if ".." in key or "/" in key or "\\" in key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Error: Path traversal characters detected in object key.",
            )
        full_path = os.path.abspath(os.path.join(self.base_dir, clean_key))
        if not full_path.startswith(self.base_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Error: Invalid storage path boundary.",
            )
        return full_path

    async def save_object(self, key: str, data: bytes) -> str:
        safe_path = self._get_safe_path(key)
        with open(safe_path, "wb") as f:
            f.write(data)
        return f"storage://local/{os.path.basename(safe_path)}"

    async def get_object(self, key: str) -> bytes:
        safe_path = self._get_safe_path(key)
        if not os.path.exists(safe_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Storage object '{key}' not found.",
            )
        with open(safe_path, "rb") as f:
            return f.read()

    async def delete_object(self, key: str) -> bool:
        safe_path = self._get_safe_path(key)
        if os.path.exists(safe_path):
            os.remove(safe_path)
            return True
        return False

    async def object_exists(self, key: str) -> bool:
        safe_path = self._get_safe_path(key)
        return os.path.exists(safe_path)


class S3StorageProvider(BaseStorageProvider):
    """
    S3/MinIO Object Storage Provider template.
    Uses mock in-memory key-store when boto3 client is not initialized.
    """

    def __init__(self, bucket: str = "cadastravision-imagery"):
        self.bucket = bucket
        self._mock_store: dict[str, bytes] = {}

    async def save_object(self, key: str, data: bytes) -> str:
        clean_key = os.path.basename(key)
        self._mock_store[clean_key] = data
        return f"s3://{self.bucket}/{clean_key}"

    async def get_object(self, key: str) -> bytes:
        clean_key = os.path.basename(key)
        if clean_key not in self._mock_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"S3 object '{key}' not found in bucket '{self.bucket}'.",
            )
        return self._mock_store[clean_key]

    async def delete_object(self, key: str) -> bool:
        clean_key = os.path.basename(key)
        if clean_key in self._mock_store:
            del self._mock_store[clean_key]
            return True
        return False

    async def object_exists(self, key: str) -> bool:
        clean_key = os.path.basename(key)
        return clean_key in self._mock_store


class StorageService:
    """
    Unified Storage Service wrapping active storage provider.
    """

    def __init__(self, provider: BaseStorageProvider | None = None):
        self.provider = provider or LocalStorageProvider()

    async def store_file(self, filename: str, data: bytes) -> str:
        return await self.provider.save_object(filename, data)

    async def read_file(self, filename: str) -> bytes:
        return await self.provider.get_object(filename)

    async def remove_file(self, filename: str) -> bool:
        return await self.provider.delete_object(filename)

    async def exists(self, filename: str) -> bool:
        return await self.provider.object_exists(filename)
