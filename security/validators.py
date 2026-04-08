#!/usr/bin/env python3
"""
WENDELL Core 33 - Request Validators
Input sanitisation and schema validation helpers.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Maximum lengths
MAX_QUERY_LEN = 4096
MAX_FIELD_LEN = 512


def validate_request_data(
    data: Dict[str, Any],
    required_fields: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate an incoming request dict.
    Returns (True, None) on success or (False, error_message) on failure.
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"

    for field in required_fields or []:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Sanitise string fields
    for key, value in data.items():
        if isinstance(value, str):
            if len(value) > MAX_QUERY_LEN:
                return False, f"Field '{key}' exceeds maximum length ({MAX_QUERY_LEN})"
            # Basic injection guard
            if re.search(r"[<>]", value):
                data[key] = re.sub(r"[<>]", "", value)

    return True, None
