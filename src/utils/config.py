"""Centralized configuration management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Groq LLM
    groq_api_key: str = ""

    # Energy APIs
    eia_api_key: str = ""
    electricity_maps_api_key: str = ""
    nrel_api_key: str = ""

    # Climate APIs
    noaa_cdo_token: str = ""
    copernicus_cds_key: str = ""

    # Environment APIs
    openaq_api_key: str = ""
    aqicn_api_token: str = ""
    openweathermap_api_key: str = ""
    global_forest_watch_api_key: str = ""

    # Agriculture APIs
    gbif_username: str = ""
    gbif_password: str = ""
    usda_nass_api_key: str = ""

    # Transport APIs
    open_charge_map_api_key: str = ""

    # Carbon APIs
    climatiq_api_key: str = ""
    moenv_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Paths
    data_dir: Path = Path("data")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
