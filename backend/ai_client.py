import os
from typing import Optional, Dict, Any
from litellm import completion
from .config import AIConfig

class UnifiedAIClient:
    """Unified client for multiple AI providers using LiteLLM."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or AIConfig.get_current_provider()
        self.config = AIConfig.get_provider_config(self.provider)
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response using the configured AI provider."""
        
        # Use default model if none specified
        if not model:
            model = self.config["default_model"]
        
        # Add model prefix if needed
        full_model = f"{self.config['model_prefix']}{model}"
        
        # Prepare parameters
        params = {
            "model": full_model,
            "messages": [{"role": "user", "content": prompt}],
            "api_key": AIConfig.get_api_key(self.provider),
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        # Add provider-specific parameters
        if "api_base_env" in self.config:
            api_base = os.getenv(self.config["api_base_env"])
            if api_base:
                params["api_base"] = api_base
        
        if "api_version_env" in self.config:
            api_version = os.getenv(self.config["api_version_env"])
            if api_version:
                params["api_version"] = api_version
        
        try:
            response = completion(**params)
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
        
        # Add provider-specific parameters
        if "api_base_env" in self.config:
            api_base = os.getenv(self.config["api_base_env"])
            if api_base:
                params["api_base"] = api_base
        
        if "api_version_env" in self.config:
            api_version = os.getenv(self.config["api_version_env"])
            if api_version:
                params["api_version"] = api_version
        
        try:
            response = completion(**params)
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
