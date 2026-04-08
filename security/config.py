#!/usr/bin/env python3
"""
WENDELL Core 33 - Centralised Configuration
Reads from environment variables with sensible defaults.
"""

import os
from typing import Any, Dict


_DEFAULTS: Dict[str, Any] = {
    # General
    "environment": "production",
    "log_level": "INFO",

    # Wendell agent
    "wendell_port": 5001,

    # JWT / Auth
    "jwt_secret": "wendell-default-secret-change-me",
    "jwt_algorithm": "HS256",
    "jwt_expiry_seconds": 3600,

    # RabbitMQ
    "rabbitmq_host": os.getenv("RABBITMQ_HOST", "localhost"),
    "rabbitmq_port": int(os.getenv("RABBITMQ_PORT", "5672")),
    "rabbitmq_user": os.getenv("RABBITMQ_USER", "guest"),
    "rabbitmq_password": os.getenv("RABBITMQ_PASSWORD", "guest"),
    "rabbitmq_vhost": os.getenv("RABBITMQ_VHOST", "/"),

    # Encryption
    "encryption_key": os.getenv("WENDELL_ENCRYPTION_KEY", ""),

    # Azure OpenAI (optional)
    "aoai_endpoint": os.getenv("AOAI_ENDPOINT", ""),
    "aoai_key": os.getenv("AOAI_KEY", ""),
    "aoai_deployment": os.getenv("AOAI_DEPLOYMENT", ""),
}


class _Config:
    """Singleton configuration store."""

    def __init__(self):
        self._store: Dict[str, Any] = dict(_DEFAULTS)
        # Override from env vars prefixed with WENDELL_
        for key in list(self._store.keys()):
            env_val = os.getenv(f"WENDELL_{key.upper()}")
            if env_val is not None:
                self._store[key] = env_val

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._store)

    def set(self, key: str, value: Any):
        self._store[key] = value


_instance: _Config | None = None


def get_config() -> _Config:
    global _instance
    if _instance is None:
        _instance = _Config()
    return _instance
