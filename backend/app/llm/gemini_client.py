"""Google Gemini client for model integration."""
import os
from typing import List, Dict, Any, Optional, Union
import json
import httpx
from pydantic import BaseModel, Field, HttpUrl
import google.generativeai as genai

from .base import BaseLLMClient
from ..utils.config import settings


class GeminiClientConfig(BaseModel):
    """Configuration for Gemini API client."""
    api_key: str = Field(..., env="GEMINI_API_KEY")
    default_model: str = Field("gemini-1.5-pro", env="GEMINI_DEFAULT_MODEL")
    timeout: int = Field(30, env="GEMINI_TIMEOUT")
    max_retries: int = Field(3, env="GEMINI_MAX_RETRIES")
    safety_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "HARASSMENT": "BLOCK_NONE",
            "HATE_SPEECH": "BLOCK_NONE",
            "SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "DANGEROUS_CONTENT": "BLOCK_NONE",
        },
        env="GEMINI_SAFETY_SETTINGS"
    )


class GeminiClient(BaseLLMClient):
    """Client for interacting with Google's Gemini models."""
    
    def __init__(self, config: Optional[GeminiClientConfig] = None):
        """Initialize the Gemini client.
        
        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or GeminiClientConfig()
        genai.configure(api_key=self.config.api_key)
        self.model = genai.GenerativeModel(self.config.default_model)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text using Google's Gemini model."""
        full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
        full_prompt += prompt
        
        try:
            response = await self.model.generate_content_async(
                contents=full_prompt,
                generation_config={
                    "temperature": min(max(0.0, temperature), 1.0),  # Clamp to 0-1
                    "max_output_tokens": min(max(1, max_tokens), 8192),  # Clamp to 1-8192
                    **kwargs
                },
                safety_settings=self.config.safety_settings
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Failed to generate content: {str(e)}")
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate chat completion using Gemini's API."""
        try:
            chat = self.model.start_chat(history=[])
            
            # Convert messages to Gemini format
            history = []
            for msg in messages:
                if msg["role"] == "system":
                    # For system messages, we'll prepend to the first user message
                    if history and history[-1]["role"] == "user":
                        history[-1]["parts"][0].text = f"{msg['content']}\n\n{history[-1]['parts'][0].text}"
                    continue
                
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
            # Send the chat history
            response = await chat.send_message_async(
                contents=history,
                generation_config={
                    "temperature": min(max(0.0, temperature), 1.0),
                    "max_output_tokens": min(max(1, max_tokens), 8192),
                    **kwargs
                },
                safety_settings=self.config.safety_settings
            )
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate chat completion: {str(e)}")
    
    async def get_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """Get embeddings using Gemini's API."""
        try:
            model = genai.GenerativeModel('models/embedding-001')
            embeddings = []
            
            for text in texts:
                result = await model.embed_content_async(text)
                embeddings.append(result['embedding'])
                
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Failed to get embeddings: {str(e)}")
    
    @classmethod
    def from_env(cls) -> 'GeminiClient':
        """Create a GeminiClient instance using environment variables."""
        return cls()