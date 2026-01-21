"""Configuration settings loaded from environment."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings from environment variables."""

    def __init__(self):
        self.rungap_path = Path(
            os.getenv(
                "RUNGAP_PATH",
                "/Users/bart/Library/Mobile Documents/iCloud~com~rungap~RunGap/Documents/Export",
            )
        )
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.database_path = Path(os.getenv("DATABASE_PATH", "./trainy.db"))

    @property
    def has_openrouter_key(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.openrouter_api_key and self.openrouter_api_key != "your-key-here")

    @property
    def rungap_exists(self) -> bool:
        """Check if RunGap export path exists."""
        return self.rungap_path.exists()


# Global settings instance
settings = Settings()
