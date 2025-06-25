"""
Roboflow client initialization with environment variable support.

This module provides a factory function to create a Roboflow InferenceHTTPClient
with configuration from environment variables or explicit parameters.
"""

import os
from typing import Optional
from inference_sdk import InferenceHTTPClient

from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_client(
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
) -> InferenceHTTPClient:
    """Create a Roboflow InferenceHTTPClient instance.
    
    Args:
        api_key: Roboflow API key. If None, reads from ROBOFLOW_API_KEY env var
        api_url: Roboflow API URL. If None, reads from ROBOFLOW_API_URL env var
        
    Returns:
        Configured InferenceHTTPClient instance
        
    Raises:
        ValueError: If api_key or api_url not provided and not in environment
    """
    # Get API key / url from env var if not provided
    api_url = api_url or os.getenv("ROBOFLOW_API_URL")
    if not api_url:
        raise ValueError(
            "Roboflow API URL must be provided either through arguments "
            "or ROBOFLOW_API_URL environment variable"
        )
    
    api_key = api_key or os.getenv("ROBOFLOW_API_KEY")        
    if not api_key:
        raise ValueError(
            "Roboflow API key must be provided either through arguments "
            "or ROBOFLOW_API_KEY environment variable"
        )
        
    # Initialize and return the client
    client = InferenceHTTPClient(
        api_url=api_url,
        api_key=api_key
    )
    logger.debug("Initialized Roboflow client")
    return client 