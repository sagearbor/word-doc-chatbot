# backend/config.py
import os
from typing import Dict, Any, Optional # Corrected import
from dotenv import load_dotenv

# Load environment variables from .env file, assuming .env is in the project root (parent of backend/)
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"[DEBUG] config.py: Loaded .env from {dotenv_path}") # Optional debug print
else:
    # Fallback to attempting to load .env from the current working directory
    # This is less predictable and might not be what you want if CWD is not project root.
    # Consider removing this else block if .env *must* be in project root relative to this file.
    if load_dotenv():
        # print("[DEBUG] config.py: Loaded .env from current working directory.") # Optional debug print
        pass
    else:
        print(f"[WARNING] config.py: .env file not found at {dotenv_path} or in current working directory. Relying on pre-set environment variables.")


class AIConfig:
    PROVIDERS: Dict[str, Dict[str, Any]] = { # Added type hint for PROVIDERS
        "azure_openai": {
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "api_base_env": "AZURE_OPENAI_ENDPOINT",
            "api_version_env": "AZURE_OPENAI_API_VERSION",
            "default_model": os.getenv("AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME", "gpt-35-turbo").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT_NAME", "gpt-4o").split('#')[0].strip().strip("'\""),
            "model_prefix": "azure/"
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "default_model": os.getenv("OPENAI_DEFAULT_MODEL_ID", "gpt-3.5-turbo").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("OPENAI_GPT4_MODEL_ID", "gpt-4-turbo-preview").split('#')[0].strip().strip("'\""),
            "model_prefix": "" # Often empty for OpenAI direct with LiteLLM
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "default_model": os.getenv("ANTHROPIC_DEFAULT_MODEL_ID", "claude-3-sonnet-20240229").split('#')[0].strip().strip("'\""),
            "model_prefix": "", # LiteLLM model name is usually complete
        },
        "google": {
            "api_key_env": "GOOGLE_API_KEY",
            "default_model": os.getenv("GOOGLE_DEFAULT_MODEL_ID", "gemini-1.5-flash-latest").split('#')[0].strip().strip("'\""),
            "model_prefix": "gemini/"
        }
        # Add a "mock" provider here if you want to test without actual API calls
        # "mock": { "api_key_env": "MOCK_KEY", "default_model": "mock_model", "model_prefix": "" }
    }

    @classmethod
    def get_current_provider(cls) -> str:
        provider = os.getenv("CURRENT_AI_PROVIDER")
        if not provider:
            print("[WARNING] AIConfig: CURRENT_AI_PROVIDER environment variable not set. Defaulting to 'azure_openai'.")
            return "azure_openai"
        
        provider_normalized = provider.split('#')[0].strip().lower()
        if provider_normalized not in cls.PROVIDERS:
            available_options = list(cls.PROVIDERS.keys())
            print(f"[ERROR] AIConfig: Unknown provider '{provider_normalized}' specified in CURRENT_AI_PROVIDER. Available: {available_options}")
            raise ValueError(f"Unknown provider: {provider_normalized}. Available: {available_options}")
        return provider_normalized

    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        provider_normalized = provider.lower()
        config = cls.PROVIDERS.get(provider_normalized)
        if config is None:
            available_options = list(cls.PROVIDERS.keys())
            print(f"[ERROR] AIConfig: Configuration for provider '{provider_normalized}' not found. Available: {available_options}")
            raise ValueError(f"Configuration for provider '{provider_normalized}' not found. Available: {available_options}")
        return config

    @staticmethod
    def get_api_key(provider_name: str) -> Optional[str]:
        try:
            provider_config = AIConfig.get_provider_config(provider_name)
        except ValueError: # Handles if provider_name is invalid
            return None # Error already printed by get_provider_config

        api_key_env_var = provider_config.get("api_key_env")
        if not api_key_env_var:
            print(f"[WARNING] AIConfig: 'api_key_env' not configured in PROVIDERS for provider '{provider_name}'. Cannot fetch API key.")
            return None
        
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            print(f"[CRITICAL WARNING] AIConfig: Environment variable '{api_key_env_var}' for provider '{provider_name}' is NOT SET. API calls will fail.")
            # For stricter behavior, you could raise an error here:
            # raise EnvironmentError(f"Required API key environment variable '{api_key_env_var}' for provider '{provider_name}' is not set.")
        return api_key

    @staticmethod
    def get_model_for_provider(provider_name: str, model_type: str = "default_model") -> str:
        """Gets a specific model type (e.g., 'default_model', 'gpt4_model') for the provider."""
        config = AIConfig.get_provider_config(provider_name)
        model_name_from_env = config.get(model_type) # This already has os.getenv fallback from PROVIDERS dict
        if not model_name_from_env: # Should not happen if fallbacks in PROVIDERS are good strings
            print(f"[WARNING] AIConfig: Model type '{model_type}' not found or env var not set for provider '{provider_name}'. Returning a generic fallback.")
            return "generic-fallback-model" 
        return model_name_from_env

class AppConfig:
    """General application configuration (not AI specific)."""
    def __init__(self):
        # Ensure .env is loaded before AppConfig tries to read from os.getenv for its own settings
        # This load_dotenv call is primarily for when AppConfig might be instantiated independently.
        # If AIConfig is always instantiated first, its load_dotenv would have already run.
        if not os.getenv("DOTENV_LOADED_BY_AICONFIG"): # Simple flag to avoid multiple loads if not necessary
            if os.path.exists(dotenv_path): load_dotenv(dotenv_path)
            elif load_dotenv(): pass # Loaded from CWD
            os.environ["DOTENV_LOADED_BY_AICONFIG"] = "true" # Mark as loaded for this session

        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    def is_production(self) -> bool:
        return self.environment == "production"

# You can create a global instance if you use AppConfig widely, or instantiate where needed.
app_settings = AppConfig()
