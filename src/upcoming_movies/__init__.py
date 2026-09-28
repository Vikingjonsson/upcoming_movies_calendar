"""Upcoming movies calendar generator package."""

from __future__ import annotations

import warnings

# Suppress urllib3 NotOpenSSLWarning on LibreSSL
warnings.filterwarnings("ignore", module="urllib3")

__all__ = ["__version__"]

__version__ = "0.1.0"
