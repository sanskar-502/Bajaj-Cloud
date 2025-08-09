# llm_providers.py

import json
from abc import ABC, abstractmethod
from typing import Dict, Any

import google.generativeai as genai
import openai
from config import Config

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        pass
    @abstractmethod
    def generate_structured_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        pass

class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation."""
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model_name)
        self.model_name = model_name

    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = self.model_instance.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error from Gemini: {str(e)}"

    def generate_structured_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        json_prompt = f"Follow these instructions: {prompt}. Output a valid JSON object only."
        try:
            config = genai.types.GenerationConfig(response_mime_type="application/json")
            response = self.model_instance.generate_content(json_prompt, generation_config=config)
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Error from Gemini: {str(e)}"}

class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider implementation."""
    def __init__(self, api_key: str, model_name: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def generate_response(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI: {str(e)}"

    def generate_structured_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"Error from OpenAI: {str(e)}"}

class LLMFactory:
    """Factory to create and configure the appropriate LLM provider."""
    _provider_instance: LLMProvider = None
    @classmethod
    def get_provider(cls) -> LLMProvider:
        if cls._provider_instance is None:
            config = Config()
            provider_type = config.LLM_PROVIDER.lower()
            if provider_type == "gemini":
                cls._provider_instance = GeminiProvider(config.GEMINI_API_KEY, config.GEMINI_MODEL)
            elif provider_type == "openai":
                cls._provider_instance = OpenAIProvider(config.OPENAI_API_KEY, config.OPENAI_MODEL)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider_type}")
        return cls._provider_instance

def get_llm_provider() -> LLMProvider:
    """Convenience function to get the singleton LLM provider instance."""
    return LLMFactory.get_provider()