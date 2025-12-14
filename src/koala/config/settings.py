"""Application settings and configuration.

# Using uv run
KOALA_DATA_FILE=~/data/argmap.json uv run koala

# Using uvx
KOALA_DATA_FILE=~/data/argmap.json uvx koala

# Multiple settings
KOALA_DATA_FILE=~/maps/debate.json KOALA_MAX_NODES=200 uv run koala
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """KOALA application settings."""
    
    # Data persistence
    data_file: Path = Path("argument_map.json")
    
    # Graph constraints
    max_nodes: int = 1000
    
    # Validation settings
    enable_auto_validation: bool = True
    
    class Config:
        env_prefix = "KOALA_"
        case_sensitive = False


# Global settings instance
settings = Settings()
