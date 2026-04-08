#!/usr/bin/env python3
"""
WENDELL Core 33 - Audit Logger
Structured audit trail for compliance and forensic review.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_audit_logger = logging.getLogger("wendell.audit")
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(message)s"))
_audit_logger.addHandler(_handler)
_audit_logger.setLevel(logging.INFO)


class AuditLogger:
    """Per-component audit logger."""

    def __init__(self, component: str):
        self.component = component

    def log(
        self,
        action: str,
        actor: str,
        target: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "component": self.component,
            "action": action,
            "actor": actor,
            "target": target,
            "details": details or {},
        }
        _audit_logger.info(json.dumps(entry))


def get_audit_logger(component: str) -> AuditLogger:
    return AuditLogger(component)
