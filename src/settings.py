from typing import Any

from dotenv import find_dotenv
from pydantic import SecretStr, computed_field
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
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Secret keys
    AUTH_SECRET: SecretStr | None = None
    JWT_ALGORITHM: str = "HS256"

    # LLM API keys
    GROQ_API_KEY: SecretStr
    GROQ_MODEL: str = "llama_31_8b"

    # Tracing for Langchain
    LANGCHAIN_TRACING_V2: bool = (
        False  # Data will be sent to Langchain for monitering and improvement, if enabled
    )
    LANGCHAIN_PROJECT: str = "default"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: SecretStr | None = None  # LangSmith API key

    def model_post_init(self, __context: Any) -> None:
        """
        Validate the settings after initialization
        """
        if self.LANGCHAIN_TRACING_V2 and self.LANGCHAIN_API_KEY is None:
            raise ValueError("Tracing is enabled, but LANGCHAIN_API_KEY is missing!")

        if self.GROQ_API_KEY is None:
            raise ValueError("GROQ_API_KEY is required! Please set it in environment.")

    @computed_field
    @property
    def BASE_URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"

    def is_dev(self) -> bool:
        return self.MODE == "dev"


settings = Settings()
