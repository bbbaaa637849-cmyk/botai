"""
Settings and configuration module for Project Aether-Human.
Defines system parameters, credential models, database connections, and psychological constants.
"""

from __future__ import annotations

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SystemSettings(BaseSettings):
    """
    Central operational settings for Aether-Human Core.
    Loads from environment variables and .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Core Application
    app_name: str = Field(default="AetherHumanCore", description="System identifier")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Standard logging level")
    debug: bool = Field(default=False, description="Debug mode flag")
    enable_sleep_ghosting: bool = Field(default=False, description="Whether bot completely ignores non-partner messages during Cairo sleep hours")

    # Gemini Multi-Key Rotation Pool
    gemini_api_keys: str = Field(
        default="",
        description="Comma-separated list of Google Gemini API keys"
    )
    gemini_default_model: str = Field(default="gemini-flash-lite-latest", description="Primary fast reasoning LLM")
    gemini_reasoning_model: str = Field(default="gemini-3.5-flash-lite", description="Deep cognitive reflection model")
    gemini_temperature: float = Field(default=0.85, description="Sampling temperature for human conversational variance")
    gemini_max_output_tokens: int = Field(default=1024, description="Max token limit per cognitive step")

    # Telegram Credentials
    telegram_api_id: int = Field(default=0, description="Telegram MTProto App API ID")
    telegram_api_hash: str = Field(default="", description="Telegram MTProto App API Hash")
    telegram_bot_token: Optional[str] = Field(default=None, description="Optional Bot API Token for fallback")
    telegram_phone_number: Optional[str] = Field(default=None, description="Phone number for MTProto Userbot login")
    telegram_session_name: str = Field(default="aether_userbot", description="SQLite/Pyrogram session file name")
    telegram_session_string: Optional[str] = Field(default=None, description="Telethon/Pyrogram StringSession if available")

    # Governance & Admins
    admin_user_ids: str = Field(default="", description="Comma-separated Telegram user IDs of Super Admins")

    # Storage & Persistence
    postgres_url: str = Field(
        default="sqlite+aiosqlite:///./aether_human.db",
        description="SQLAlchemy async DB URL (PostgreSQL asyncpg or SQLite aiosqlite)"
    )
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="aether_secret_pass", description="Neo4j password")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant vector engine endpoint")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API Key")
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis working memory cache & queue")

    # Multimodal Services
    comfyui_host: str = Field(default="127.0.0.1", description="ComfyUI host for visual identity synthesis")
    comfyui_port: int = Field(default=8188, description="ComfyUI HTTP port")
    elevenlabs_api_key: Optional[str] = Field(default=None, description="ElevenLabs API key for ultra-realistic TTS")
    elevenlabs_voice_id: Optional[str] = Field(default=None, description="Voice ID for character tone")
    whisper_model_size: str = Field(default="large-v3", description="Local or remote Whisper model dimension")

    # Admin Observatory
    admin_host: str = Field(default="0.0.0.0", description="Admin Observatory binding host")
    admin_port: int = Field(default=8000, description="Admin Observatory HTTP/WS port")
    admin_secret_token: str = Field(default="aether_observatory_master_key_2026", description="Auth token for dashboard")

    # Psychological Baselines & Constants
    hormone_decay_rate: float = Field(default=0.03, description="Hourly decay rate of acute hormones back to homeostasis")
    typing_speed_wpm_base: int = Field(default=45, description="Average human typing speed in words per minute")
    typo_base_probability: float = Field(default=0.04, description="Base likelihood of introducing a keyboard typo")
    seen_delay_min_seconds: float = Field(default=1.5, description="Minimum delay before marking a message as read")
    seen_delay_max_seconds: float = Field(default=12.0, description="Maximum delay before marking a message as read")

    @field_validator("gemini_api_keys", mode="before")
    @classmethod
    def clean_api_keys(cls, v: object) -> str:
        if isinstance(v, list):
            return ",".join(str(item).strip() for item in v if str(item).strip())
        if isinstance(v, str):
            return v.strip()
        return ""

    @field_validator("postgres_url", mode="before")
    @classmethod
    def clean_db_url(cls, v: object) -> str:
        env_db = os.environ.get("DATABASE_URL")
        target = str(env_db or v or "sqlite+aiosqlite:///./aether_human.db").strip()
        if target.startswith("postgres://"):
            return target.replace("postgres://", "postgresql+asyncpg://", 1)
        if target.startswith("postgresql://") and not target.startswith("postgresql+asyncpg://"):
            return target.replace("postgresql://", "postgresql+asyncpg://", 1)
        return target

    @field_validator("admin_port", mode="before")
    @classmethod
    def clean_port(cls, v: object) -> int:
        railway_port = os.environ.get("PORT")
        if railway_port:
            try:
                return int(railway_port)
            except ValueError:
                pass
        return int(v) if v else 8000

    @property
    def gemini_keys_list(self) -> List[str]:
        """
        Parses the comma-delimited Gemini API keys into a sanitized list of distinct keys.
        """
        if not self.gemini_api_keys:
            return []
        keys = [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]
        return keys

    @property
    def super_admin_ids_list(self) -> List[int]:
        """
        Parses comma-delimited admin_user_ids into a list of integer Telegram IDs.
        """
        if not self.admin_user_ids:
            return []
        ids: List[int] = []
        for x in str(self.admin_user_ids).split(","):
            x = x.strip()
            if x.isdigit():
                ids.append(int(x))
        return ids


# Singleton global instance
settings = SystemSettings()
