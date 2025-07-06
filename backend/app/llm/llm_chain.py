"""Dual LLM chain for Nova Chatbot.

This module implements the dual-LLM architecture where:
1. Gemini handles analysis, planning, and memory operations
2. Groq/LLaMA generates the final user-facing response
"""
from typing import Dict, List, Optional, Any, Union
import json
import logging
from enum import Enum

from pydantic import BaseModel, Field

from .factory import get_llm_client, LLMProvider
from .base import BaseLLMClient

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """Structured result from the analysis phase with Gemini."""
    # Core analysis components
    key_points: List[str] = Field(
        ...,
        description="List of key points or facts extracted from the conversation"
    )
    required_context: List[str] = Field(
        default_factory=list,
        description="Any additional context needed from the conversation history"
    )
    response_style: str = Field(
        "friendly",
        description="Tone/style for the response (e.g., friendly, professional, witty)"
    )
    needs_memory_update: bool = Field(
        False,
        description="Whether this interaction should update the conversation memory"
    )
    # Additional metadata for the response generator
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the response generator"
    )


class DualLLMChain:
    """Orchestrates the dual-LLM architecture for Nova Chatbot."""
    
    def __init__(self):
        self.analyzer = None  # Will be initialized as Gemini
        self.generator = None  # Will be initialized as Groq/LLaMA
        self._initialized = False
    
    async def initialize(self):
        """Initialize both LLM clients."""
        if not self._initialized:
            self.analyzer = await get_llm_client(provider=LLMProvider.GEMINI)
            self.generator = await get_llm_client(provider=LLMProvider.GROQ)
            self._initialized = True
    
    async def analyze_with_gemini(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> AnalysisResult:
        """Use Gemini to analyze the message and conversation context."""
        if not self._initialized:
            await self.initialize()
        
        # Prepare the analysis prompt
        prompt = """
        You are the analysis engine for Nova Chatbot. Your task is to analyze the user's message 
        and conversation context to prepare for generating a helpful response.
        
        Conversation History:
        {history}
        
        User Message: {message}
        
        Your analysis should include:
        1. Key points or facts from the message
        2. Any required context from the conversation history
        3. The appropriate response style/tone
        4. Whether this interaction should be added to the conversation memory
        
        Respond with a JSON object containing:
        {{
            "key_points": ["list", "of", "key", "points"],
            "required_context": ["relevant", "context", "from", "history"],
            "response_style": "friendly|professional|witty|etc",
            "needs_memory_update": true|false,
            "metadata": {{
                // Any additional metadata for the response generator
            }}
        }}
        """.format(
            history="\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-5:]]),
            message=user_message
        )
        
        try:
            # Get the raw analysis from Gemini
            response = await self.analyzer.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=1000,
                **kwargs
            )
            
            # Parse the JSON response
            try:
                # Sometimes the response might include markdown code blocks
                if '```json' in response:
                    json_str = response.split('```json')[1].split('```')[0].strip()
                else:
                    json_str = response.strip()
                
                analysis_data = json.loads(json_str)
                return AnalysisResult(**analysis_data)
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse analysis result: {e}")
                # Fallback to a basic analysis
                return AnalysisResult(
                    key_points=[user_message],
                    required_context=[],
                    response_style="friendly",
                    needs_memory_update=False
                )
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # If analysis fails, just pass through the message
            return AnalysisResult(
                key_points=[user_message],
                required_context=[],
                response_style="friendly",
                needs_memory_update=False
            )
    
    async def generate_with_groq(
        self,
        user_message: str,
        analysis: AnalysisResult,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Use Groq/LLaMA to generate a response based on Gemini's analysis."""
        if not self._initialized:
            await self.initialize()
        
        # Prepare the system prompt with analysis results
        system_prompt = f"""
        You are Nova, a helpful AI assistant. Below is an analysis of the user's message:
        
        Key Points:
        {chr(10).join(f"- {point}" for point in analysis.key_points)}
        
        Context from Conversation:
        {chr(10).join(f"- {ctx}" for ctx in analysis.required_context) if analysis.required_context else 'No specific context needed.'}
        
        Response Style: {analysis.response_style}
        
        Please respond to the user in a {analysis.response_style} manner.
        """.strip()
        
        # Prepare the conversation history for the generator
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history[-5:],  # Include recent conversation history
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Generate the response using Groq/LLaMA
            response = await self.generator.generate_chat(
                messages=messages,
                temperature=0.7,  # Slightly higher temperature for more creative responses
                max_tokens=1000,
                **kwargs
            )
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            # Fallback response if generation fails
            return "I'm having trouble generating a response right now. Could you please rephrase your question?"
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Process a message through the dual-LLM chain."""
        # Step 1: Analyze with Gemini
        analysis = await self.analyze_with_gemini(
            user_message=user_message,
            conversation_history=conversation_history,
            **kwargs.get('analysis_kwargs', {})
        )
        
        # Step 2: Generate response with Groq/LLaMA
        response = await self.generate_with_groq(
            user_message=user_message,
            analysis=analysis,
            conversation_history=conversation_history,
            **kwargs.get('generation_kwargs', {})
        )
        
        # Step 3: Update conversation memory if needed
        if analysis.needs_memory_update:
            # TODO: Implement memory update logic
            pass
        
        return response
