"""LLM module for Nova Chatbot.

This module provides interfaces and implementations for various LLM providers
and the dual-LLM chain architecture.
"""
from .base import BaseLLMClient
from .groq_client import GroqClient
from .gemini_client import GeminiClient
from .llm_chain import DualLLMChain, AnalysisResult
from .factory import (
    LLMProvider,
    LLMFactory,
    get_llm_client,
    close_llm_clients
)

__all__ = [
    # Base and clients
    'BaseLLMClient',
    'GroqClient',
    'GeminiClient',
    
    # Dual LLM Chain
    'DualLLMChain',
    'AnalysisResult',
    
    # Factory and enums
    'LLMProvider',
    'LLMFactory',
    'get_llm_client',
    'close_llm_clients'
]