"""Groq client for LLaMA model integration."""
import os
from typing import List, Dict, Any, Optional, Union
import json
import httpx
from pydantic import BaseModel, Field

from .base import BaseLLMClient
from ..utils.config import settings


class GroqClientConfig(BaseModel):
    """Configuration for Groq API client."""
    api_key: str = Field(..., env="GROQ_API_KEY")
    base_url: str = Field("https://api.groq.com/openai/v1", env="GROQ_API_BASE_URL")
    default_model: str = Field("llama3-70b-8192", env="GROQ_DEFAULT_MODEL")
    timeout: int = Field(30, env="GROQ_TIMEOUT")
    max_retries: int = Field(3, env="GROQ_MAX_RETRIES")


class GroqClient(BaseLLMClient):
    """Client for interacting with Groq's LLaMA models."""
    
    def __init__(self, config: Optional[GroqClientConfig] = None):
        """Initialize the Groq client.
        
        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or GroqClientConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.config.timeout,
            follow_redirects=True
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text using Groq's LLaMA model."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        return await self.generate_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate chat completion using Groq's API."""
        payload = {
            "model": self.config.default_model,
            "messages": messages,
            "temperature": min(max(0.0, temperature), 2.0),  # Clamp to 0-2
            "max_tokens": min(max(1, max_tokens), 8192),  # Clamp to 1-8192
            **kwargs
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
            except (httpx.HTTPStatusError, json.JSONDecodeError) as e:
                if attempt == self.config.max_retries - 1:
                    raise RuntimeError(
                        f"Failed to generate completion after {self.config.max_retries} attempts: {str(e)}"
                    )
                continue
    
    async def get_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """Get embeddings using Groq's API."""
        # Groq doesn't currently offer an embeddings endpoint
        # This is a placeholder for future implementation
        raise NotImplementedError("Embeddings are not currently supported by Groq API")
    
    @classmethod
    def from_env(cls) -> 'GroqClient':
        """Create a GroqClient instance using environment variables."""
        return cls()