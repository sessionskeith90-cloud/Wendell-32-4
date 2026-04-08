#!/usr/bin/env python3
"""
WENDELL Core 33 - Authentication
JWT-based token authentication for Flask routes.
"""

import functools
import logging
from typing import Callable

import jwt
from flask import request, jsonify

from security.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


def _decode_token(token: str) -> dict:
    """Decode and verify a JWT."""
    return jwt.decode(
        token,
        config.get("jwt_secret"),
        algorithms=[config.get("jwt_algorithm", "HS256")],
    )


def create_token(payload: dict) -> str:
    """Create a signed JWT."""
    import time

    payload.setdefault("exp", int(time.time()) + config.get("jwt_expiry_seconds", 3600))
    return jwt.encode(
        payload,
        config.get("jwt_secret"),
        algorithm=config.get("jwt_algorithm", "HS256"),
    )


def token_required(fn: Callable) -> Callable:
    """Flask route decorator that enforces a valid Bearer token."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as exc:
            logger.warning(f"Invalid token: {exc}")
            return jsonify({"error": "Invalid token"}), 401
        return fn(*args, **kwargs)

    return wrapper
