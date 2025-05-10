"""
Configuration module for the Circuit Breakers Team Hub application.
Provides environment and path configuration functionality.
"""

import os

def configure_environment():
    """
    Sets up environment variables for the application.
    In this version, we don't need database configuration.
    """
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("assets", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/resources", exist_ok=True)
    os.makedirs("uploads/media", exist_ok=True)
    
    # Ensure any other needed environment variables are set
    if "CIRCUIT_BREAKERS_ENV" not in os.environ:
        os.environ["CIRCUIT_BREAKERS_ENV"] = "production"
