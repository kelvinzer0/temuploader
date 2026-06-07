"""
temuploader - Temporary file uploader with automatic fallback
Supports multiple providers, auto-retry, and smart provider selection.
"""

from .core import upload, upload_text, upload_file, list_providers, get_provider
from .providers import PROVIDERS

__version__ = "0.2.0"
__all__ = [
    "upload",
    "upload_text",
    "upload_file",
    "list_providers",
    "get_provider",
    "PROVIDERS",
]
