import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AIConfig:
    """Configuration for AI providers with LiteLLM integration."""
    
    PROVIDERS = {
        "openai": {
            "model_prefix": "",
            "api_key_env": "OPENAI_API_KEY",
            "default_model": "gpt-4"
        },
        "azure_openai": {
            "model_prefix": "azure/",
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "api_base_env": "AZURE_OPENAI_ENDPOINT",
            "api_version_env": "AZURE_OPENAI_API_VERSION",
            "default_model": "gpt-4"
        },
        "anthropic": {
            "model_prefix": "",
            "api_key_env": "ANTHROPIC_API_KEY",
            "default_model": "claude-3-sonnet-20240229"
        },
        "google": {
            "model_prefix": "gemini/",
            "api_key_env": "GOOGLE_API_KEY",
            "default_model": "gemini-pro"
        }
    }
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        if provider not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls.PROVIDERS.keys())}")
        return cls.PROVIDERS[provider]
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """Get API key for a specific provider."""
        config = cls.get_provider_config(provider)
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise ValueError(f"API key not found for provider '{provider}'. Set {config['api_key_env']} environment variable.")
        return api_key
    
    @classmethod
    def get_current_provider(cls) -> str:
        """Get the currently configured provider."""
        return os.getenv("AI_PROVIDER", "openai")

class AppConfig:
    """General application configuration."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.ai_provider = os.getenv("AI_PROVIDER", "openai")
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    def is_production(self) -> bool:
        return self.environment == "production"

# Global config instance
app_config = AppConfig()
