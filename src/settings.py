"""
This module defines the environment-specific configuration settings for the DAPA application.
It uses Pydantic's BaseSettings to load and validate settings from environment variables.
"""

import os
from typing import Any, List

from dotenv import find_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Environment specific configuration
    """

    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )
    # path
    MODE: str | None = None  # dev, prod

    # Ports
    SERVER_PORT: int
    CLIENT_PORT: int

    # Secret keys
    AUTH_SECRET: SecretStr | None = None
    JWT_ALGORITHM: str = "HS256"

    # LLM API keys
    GROQ_API_KEY: SecretStr
    GROQ_MODEL: str = "llama3-8b-8192"
    GROQ_MODEL_TEMP: float = 0.5

    # Tracing for Langchain
    LANGCHAIN_TRACING_V2: bool = (
        False  # Data will be sent to Langchain for monitering and improvement, If enabled.
    )
    LANGCHAIN_PROJECT: str = "default_dapa"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: SecretStr | None = None  # LangSmith API key

    # DB
    DATABASE_URL: SecretStr

    # Redis
    REDIS_URL: str

    # API LIMITS
    API_RATE_LIMIT_PER_DAY: int = 12

    # Security
    ALLOWED_HOSTS: str = ""  # Comma-separated allowed hosts

    # Logging
    LOG_LEVEL: str = "INFO"  # Allowed: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_ROTATION: str = "7 days"
    LOG_FILE: str = "dapa_be.log"

    def model_post_init(self, __context: Any) -> None:
        """
        Validate the settings after initialization
        """
        if self.LANGCHAIN_TRACING_V2 and self.LANGCHAIN_API_KEY is None:
            raise ValueError("Tracing is enabled, but LANGCHAIN_API_KEY is missing!")

        if self.GROQ_API_KEY is None:
            raise ValueError(
                "GROQ_API_KEY is required! This key enables the application to connect with an advanced language model that understands queries and provides intelligent responses. You can generate your API at https://console.groq.com/keys ."
            )

    def is_dev(self) -> bool:
        """checks if the application is running in development mode"""
        return self.MODE == "dev"

    @property
    def root_path(self) -> str:
        """returns the root path of the project"""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @property
    def allowed_hosts(self) -> List[str]:
        """Parses ALLOWED_HOSTS from a comma-separated string into a list."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host]


settings = Settings()
