#!/usr/bin/env python3
"""
WENDELL Core 33 - Encryption Manager
Fernet-based symmetric encryption for data at rest.
"""

import base64
import hashlib
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet

from security.config import get_config

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Symmetric encryption using Fernet."""

    def __init__(self, key: Optional[str] = None):
        raw = key or get_config().get("encryption_key") or ""
        if raw:
            # Derive a 32-byte key from arbitrary-length secret
            derived = hashlib.sha256(raw.encode()).digest()
            self._fernet = Fernet(base64.urlsafe_b64encode(derived))
        else:
            # Auto-generate (ephemeral – fine for dev, not for prod persistence)
            self._fernet = Fernet(Fernet.generate_key())
            logger.warning("Using ephemeral encryption key – set WENDELL_ENCRYPTION_KEY for persistence")

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()


_instance: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    global _instance
    if _instance is None:
        _instance = EncryptionManager()
    return _instance
