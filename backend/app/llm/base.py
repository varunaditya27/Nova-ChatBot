"""Base LLM client interface and common functionality."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: The input prompt
            system_prompt: Optional system message to set behavior
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate chat completion from a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated message content
        """
        pass
    
    @abstractmethod
    async def get_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """Get embeddings for a list of texts.
        
        Args:
            texts: List of input texts
            **kwargs: Additional model-specific parameters
            
        Returns:
            List of embedding vectors
        """
        pass
