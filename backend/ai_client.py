import os
import os # Import os to set environment variables
from typing import Optional, Dict, Any
import litellm # Import the base module
from .config import AIConfig

os.environ['LITELLM_LOG'] = 'DEBUG' # Recommended way to enable LiteLLM debug logs

class UnifiedAIClient:
    """Unified client for multiple AI providers using LiteLLM."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or AIConfig.get_current_provider()
        self.config = AIConfig.get_provider_config(self.provider)
        print(f"[DEBUG] UnifiedAIClient initialized with provider='{self.provider}' "
              f"and API key var='{self.config.get('api_key_env')}'")
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using the configured AI provider."""
        
        if not model:
            model = self.config["default_model"]
        
        full_model = f"{self.config['model_prefix']}{model}"
        
        params = {
            "model": full_model,
            "messages": [{"role": "user", "content": prompt}],
            "api_key": AIConfig.get_api_key(self.provider),
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        if "api_base_env" in self.config:
            api_base = os.getenv(self.config["api_base_env"])
            if api_base:
                params["api_base"] = api_base
        
        if "api_version_env" in self.config:
            raw_api_version = os.getenv(self.config["api_version_env"])
            raw_api_version = os.getenv(self.config["api_version_env"])
            if raw_api_version:
                # Clean the version string:
                # 1. Take part before any '#' comment
                # 2. Strip leading/trailing whitespace
                # 3. Strip all leading/trailing quote characters (' and ")
                temp_version = raw_api_version.split('#')[0].strip()
                # Iteratively strip quotes in case of mixed or multiple quotes like "'value'"
                while len(temp_version) > 1 and temp_version[0] in ("'", "\"") and temp_version[-1] in ("'", "\""):
                    temp_version = temp_version[1:-1]
                cleaned_api_version = temp_version.strip("'\"") # Final strip for single quotes

                print(f"[AI_CLIENT_DEBUG] Raw api_version from env: '{raw_api_version}'") # DEBUG
                print(f"[AI_CLIENT_DEBUG] Cleaned api_version: '{cleaned_api_version}' (Type: {type(cleaned_api_version)})") # DEBUG
                params["api_version"] = cleaned_api_version
        
        # Fix for GPT-5 models: they only support temperature=1
        if "gpt-5" in full_model.lower() and "temperature" in params:
            if params["temperature"] == 0.0:
                print(f"[AI_CLIENT_DEBUG] Adjusting temperature from 0.0 to 1.0 for GPT-5 model")
                params["temperature"] = 1.0

        try:
            print(f"[AI_CLIENT_DEBUG] Params to litellm.completion (generate_response): {params}") # DEBUG
            response = litellm.completion(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error calling {self.provider} API: {str(e)}")
    
    def chat_completion(
        self,
        messages: list,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a chat completion response."""
        
        if not model:
            model = self.config["default_model"]
        
        full_model = f"{self.config['model_prefix']}{model}"
        
        params = {
            "model": full_model,
            "messages": messages,
            "api_key": AIConfig.get_api_key(self.provider),
            **kwargs
        }
        
        if "api_base_env" in self.config:
            api_base = os.getenv(self.config["api_base_env"])
            if api_base:
                params["api_base"] = api_base
        
        if "api_version_env" in self.config:
            raw_api_version = os.getenv(self.config["api_version_env"])
            raw_api_version = os.getenv(self.config["api_version_env"])
            if raw_api_version:
                # Clean the version string:
                # 1. Take part before any '#' comment
                # 2. Strip leading/trailing whitespace
                # 3. Strip all leading/trailing quote characters (' and ")
                temp_version = raw_api_version.split('#')[0].strip()
                # Iteratively strip quotes in case of mixed or multiple quotes like "'value'"
                while len(temp_version) > 1 and temp_version[0] in ("'", "\"") and temp_version[-1] in ("'", "\""):
                    temp_version = temp_version[1:-1]
                cleaned_api_version = temp_version.strip("'\"") # Final strip for single quotes
                
                print(f"[AI_CLIENT_DEBUG] Raw api_version from env (chat): '{raw_api_version}'") # DEBUG
                print(f"[AI_CLIENT_DEBUG] Cleaned api_version (chat): '{cleaned_api_version}' (Type: {type(cleaned_api_version)})") # DEBUG
                params["api_version"] = cleaned_api_version
        
        # Fix for GPT-5 models: they only support temperature=1
        if "gpt-5" in full_model.lower() and "temperature" in params:
            if params["temperature"] == 0.0:
                print(f"[AI_CLIENT_DEBUG] Adjusting temperature from 0.0 to 1.0 for GPT-5 model")
                params["temperature"] = 1.0

        try:
            print(f"[AI_CLIENT_DEBUG] Params to litellm.completion (chat_completion): {params}") # DEBUG
            response = litellm.completion(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error calling {self.provider} API: {str(e)}")

# Convenience functions
def get_ai_response(prompt: str, provider: Optional[str] = None, **kwargs) -> str:
    """Quick function to get AI response with current or specified provider."""
    client = UnifiedAIClient(provider)
    return client.generate_response(prompt, **kwargs)

def get_chat_response(messages: list, provider: Optional[str] = None, **kwargs) -> str:
    """Quick function to get chat completion with current or specified provider."""
    client = UnifiedAIClient(provider)
    return client.chat_completion(messages, **kwargs)
