"""Application settings and configuration.

# Using uv run
KOALA_DATA_FILE=~/data/argmap.json uv run cedrus

# Using uvx
KOALA_DATA_FILE=~/data/argmap.json uvx cedrus

# Multiple settings
KOALA_DATA_FILE=~/maps/debate.json KOALA_MAX_NODES=200 uv run cedrus
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """KOALA application settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="KOALA_",
        case_sensitive=False
    )

    # Data persistence
    data_file: Path = Path("argument_map.json")
    
    # Graph constraints
    max_nodes: int = 1000
    
    # Validation settings
    enable_auto_validation: bool = False


# Global settings instance
settings = Settings()
