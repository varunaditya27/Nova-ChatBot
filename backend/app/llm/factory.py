"""Factory for creating and managing LLM clients."""
from typing import Optional, Type, Dict, Any
from enum import Enum

from .base import BaseLLMClient
from .groq_client import GroqClient
from .gemini_client import GeminiClient
from ..utils.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    GEMINI = "gemini"


class LLMFactory:
    """Factory class for creating and managing LLM clients."""
    
    _clients: Dict[LLMProvider, BaseLLMClient] = {}
    
    @classmethod
    async def get_client(
        cls,
        provider: LLMProvider = LLMProvider.GROQ,
        **kwargs
    ) -> BaseLLMClient:
        """Get or create an LLM client instance.
        
        Args:
            provider: The LLM provider to use
            **kwargs: Additional arguments to pass to the client constructor
            
        Returns:
            An instance of the requested LLM client
            
        Raises:
            ValueError: If an unsupported provider is specified
        """
        if provider not in cls._clients:
            if provider == LLMProvider.GROQ:
                cls._clients[provider] = GroqClient()
            elif provider == LLMProvider.GEMINI:
                cls._clients[provider] = GeminiClient()
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
            
        return cls._clients[provider]
    
    @classmethod
    async def close_all(cls):
        """Close all active LLM client connections."""
        for client in cls._clients.values():
            if hasattr(client, 'close') and callable(client.close):
                await client.close()
        cls._clients.clear()


# Default client functions for convenience
async def get_llm_client(provider: LLMProvider = LLMProvider.GROQ, **kwargs) -> BaseLLMClient:
    """Get an LLM client instance.
    
    Args:
        provider: The LLM provider to use (default: groq)
        **kwargs: Additional arguments to pass to the client constructor
        
    Returns:
        An instance of the requested LLM client
    """
    return await LLMFactory.get_client(provider=provider, **kwargs)


async def close_llm_clients():
    """Close all active LLM client connections."""
    await LLMFactory.close_all()
