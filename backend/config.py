# word_processing_backend/app_main/config.py
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file, assuming .env is in the project root (word_processing_backend/)
# Adjust the path to go up one level from app_main to the project root where .env should be.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

# print(f"[DEBUG] config.py: Trying to load .env from: {dotenv_path}") # Optional debug

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"[DEBUG] config.py: Loaded .env from {dotenv_path}")
else:
    # Fallback for environments where .env might be in the CWD (less common for structured projects)
    if load_dotenv():
        # print("[DEBUG] config.py: Loaded .env from current working directory.")
        pass
    else:
        print(f"[WARNING] config.py: .env file not found at {dotenv_path} or in current working directory. Relying on pre-set environment variables if any.")


class AIConfig:
    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "azure_openai": {
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "api_base_env": "AZURE_OPENAI_ENDPOINT",
            "api_version_env": "AZURE_OPENAI_API_VERSION",
            "default_model": os.getenv("AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME", "gpt-35-turbo").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT_NAME", "gpt-4o").split('#')[0].strip().strip("'\""),
            "model_prefix": "azure/" # LiteLLM uses this prefix for Azure models
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "default_model": os.getenv("OPENAI_DEFAULT_MODEL_ID", "gpt-3.5-turbo").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("OPENAI_GPT4_MODEL_ID", "gpt-4-turbo-preview").split('#')[0].strip().strip("'\""),
            "model_prefix": "" # No prefix needed for standard OpenAI models with LiteLLM
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "default_model": os.getenv("ANTHROPIC_DEFAULT_MODEL_ID", "claude-3-sonnet-20240229").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("ANTHROPIC_CLAUDE_3_OPUS_MODEL_ID", "claude-3-opus-20240229").split('#')[0].strip().strip("'\""), # Example for a higher-tier model
            "model_prefix": "", # LiteLLM model name is usually complete
        },
        "google": { # For Gemini models via Vertex AI or Google AI Studio
            "api_key_env": "GOOGLE_API_KEY", # This is for Google AI Studio. Vertex might use ADC.
            "default_model": os.getenv("GOOGLE_DEFAULT_MODEL_ID", "gemini-1.5-flash-latest").split('#')[0].strip().strip("'\""),
            "gpt4_model": os.getenv("GOOGLE_GEMINI_1_5_PRO_MODEL_ID", "gemini-1.5-pro-latest").split('#')[0].strip().strip("'\""), # Example
            "model_prefix": "gemini/" # LiteLLM uses this prefix for Gemini models
        }
    }

    @classmethod
    def get_current_provider(cls) -> str:
        provider = os.getenv("CURRENT_AI_PROVIDER")
        if not provider:
            print("[WARNING] AIConfig: CURRENT_AI_PROVIDER environment variable not set. Defaulting to 'openai'.")
            return "openai" # Defaulting to openai if not set
        
        provider_normalized = provider.split('#')[0].strip().lower()
        if provider_normalized not in cls.PROVIDERS:
            available_options = list(cls.PROVIDERS.keys())
            print(f"[ERROR] AIConfig: Unknown provider '{provider_normalized}' specified in CURRENT_AI_PROVIDER. Available: {available_options}")
            raise ValueError(f"Unknown provider: {provider_normalized}. Available: {available_options}")
        return provider_normalized

    @classmethod
    def get_provider_config(cls, provider: Optional[str] = None) -> Dict[str, Any]:
        if provider is None:
            provider = cls.get_current_provider() # Get current provider if none specified
        else:
            provider = provider.lower()

        config = cls.PROVIDERS.get(provider)
        if config is None:
            available_options = list(cls.PROVIDERS.keys())
            print(f"[ERROR] AIConfig: Configuration for provider '{provider}' not found. Available: {available_options}")
            raise ValueError(f"Configuration for provider '{provider}' not found. Available: {available_options}")
        return config

    @staticmethod
    def get_api_key(provider_name: Optional[str] = None) -> Optional[str]:
        if provider_name is None:
            provider_name = AIConfig.get_current_provider()
        
        try:
            provider_config = AIConfig.get_provider_config(provider_name)
        except ValueError:
            return None

        api_key_env_var = provider_config.get("api_key_env")
        if not api_key_env_var:
            # For some providers (like Vertex AI on GCP using Application Default Credentials),
            # an explicit API key might not be needed if auth is handled differently.
            # print(f"[INFO] AIConfig: 'api_key_env' not configured in PROVIDERS for provider '{provider_name}'. This might be normal for some auth methods.")
            return None 
        
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            print(f"[CRITICAL WARNING] AIConfig: Environment variable '{api_key_env_var}' for provider '{provider_name}' is NOT SET. API calls might fail if this key is required.")
        return api_key

    @staticmethod
    def get_model_for_provider(provider_name: Optional[str] = None, model_type: str = "default_model") -> str:
        if provider_name is None:
            provider_name = AIConfig.get_current_provider()
        
        config = AIConfig.get_provider_config(provider_name)
        # The os.getenv in PROVIDERS definition already handles fallback to a default string
        model_name_from_config = config.get(model_type)
        
        if not model_name_from_config: # Should not happen if PROVIDERS dict has good fallbacks
            print(f"[WARNING] AIConfig: Model type '{model_type}' not found for provider '{provider_name}'. Returning a generic fallback model name.")
            return "generic-fallback-model" 
        return model_name_from_config

class AppConfig:
    def __init__(self):
        # Ensure .env is loaded. AIConfig might have done it, but this ensures it if AppConfig is used alone.
        if not os.getenv("DOTENV_LOADED_FLAG_SET_BY_AICONFIG_OR_APPCONFIG"): # Simple flag
            if os.path.exists(dotenv_path): load_dotenv(dotenv_path)
            elif load_dotenv(): pass # Loaded from CWD
            os.environ["DOTENV_LOADED_FLAG_SET_BY_AICONFIG_OR_APPCONFIG"] = "true"

        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug_mode = os.getenv("APP_DEBUG_MODE", "false").lower() == "true" # Renamed to avoid clash with LiteLLM's DEBUG_MODE
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    def is_production(self) -> bool:
        return self.environment == "production"

app_settings = AppConfig()
