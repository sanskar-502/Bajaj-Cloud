import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import google.generativeai as genai
from openai import AsyncOpenAI

from policymind.core.config import Settings


class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_structured_response(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model_name)
        self.model_name = model_name

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        response = await self.model_instance.generate_content_async(prompt)
        return response.text

    async def generate_structured_response(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        json_prompt = f"Follow these instructions: {prompt}. Output a valid JSON object only."
        config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = await self.model_instance.generate_content_async(json_prompt, generation_config=config)
        return json.loads(response.text)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def generate_structured_response(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an assistant designed to output JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")


def get_llm_provider(settings: Settings) -> LLMProvider:
    provider_type = settings.LLM_PROVIDER
    if provider_type == "gemini":
        return GeminiProvider(settings.GEMINI_API_KEY or "", settings.GEMINI_MODEL)
    if provider_type == "openai":
        return OpenAIProvider(settings.OPENAI_API_KEY or "", settings.OPENAI_MODEL)
    raise ValueError(f"Unsupported LLM provider: {provider_type}")

