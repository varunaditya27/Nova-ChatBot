"""
Topic analysis service for identifying and managing conversation topics.
Uses cosine similarity to group related messages into topics.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

from app.services.firebase_service import FirebaseService
from app.utils.cache import cached, cache_manager

logger = logging.getLogger(__name__)

class TopicService:
    """Service for managing conversation topics using cosine similarity."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.topics = {}  # In-memory store for topic metadata
        self._initialized = False
        logger.info("TopicService initialized")

    async def initialize(self):
        """Initialize the topic service by loading existing topics."""
        if not self._initialized:
            # Load existing topics from cache or database
            await self._load_topics()
            self._initialized = True
    
    async def _load_topics(self):
        """Load topics from cache or database."""
        # This is a placeholder. In a real app, you'd load topics from a persistent store.
        self.topics = {}
    
    @cached(key_prefix="topic_analysis", namespace="topics")
    async def analyze_message_topic(
        self, 
        message_id: str, 
        content: str, 
        user_id: str,
        threshold: float = 0.3
    ) -> Optional[str]:
        """
        Analyze a message and assign it to a topic.
        
        Args:
            message_id: ID of the message to analyze
            content: Text content of the message
            user_id: ID of the user who sent the message
            threshold: Similarity threshold for topic matching
            
        Returns:
            str: ID of the assigned topic, or None if no match
        """
        try:
            # Get recent messages for context
            recent_messages = await self._get_recent_messages(user_id)
            
            if not recent_messages:
                return None
                
            # Prepare texts for analysis
            texts = [msg["content"] for msg in recent_messages]
            texts.append(content)  # Add current message
            
            # Run vectorization and similarity analysis in thread pool
            loop = asyncio.get_running_loop()
            topic_id = await loop.run_in_executor(
                self.executor,
                self._find_similar_topic,
                texts,
                threshold
            )
            
            # If no similar topic found, create a new one
            if not topic_id:
                topic_id = f"topic_{user_id}_{len(self.topics) + 1}"
                self.topics[topic_id] = {
                    "keywords": self._extract_keywords(content),
                    "message_count": 0,
                    "last_updated": asyncio.get_event_loop().time(),
                    "user_id": user_id
                }
            
            # Update message with topic ID
            await self._update_message_topic(message_id, topic_id)
            
            # Update topic metadata
            await self._update_topic_metadata(topic_id)
            
            # Invalidate related caches
            await self._invalidate_topic_caches(user_id, topic_id)
            
            return topic_id
            
        except Exception as e:
            logger.error(f"Error analyzing message topic: {str(e)}")
            return None
    
    async def _get_recent_messages(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages for a user with caching."""
        cache_key = cache_manager.get_cache_key("recent_messages", user_id=user_id, limit=limit)
        cached_messages = await cache_manager.get(cache_key)
        
        if cached_messages is not None:
            return cached_messages
            
        messages = await FirebaseService.get_messages(user_id=user_id, limit=limit)
        await cache_manager.set(cache_key, messages)
        return messages
    
    async def _update_message_topic(self, message_id: str, topic_id: str):
        """Update a message's topic with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await FirebaseService.update_message(
                    message_id=message_id,
                    update_data={"topic_id": topic_id}
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to update message topic after {max_retries} attempts: {str(e)}")
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
    
    async def _update_topic_metadata(self, topic_id: str):
        """Update topic metadata in memory and cache."""
        if topic_id in self.topics:
            self.topics[topic_id]["message_count"] += 1
            self.topics[topic_id]["last_updated"] = asyncio.get_event_loop().time()
            
            # Update topic in cache
            cache_key = cache_manager.get_cache_key("topic", topic_id=topic_id)
            await cache_manager.set(cache_key, self.topics[topic_id])
    
    async def _invalidate_topic_caches(self, user_id: str, topic_id: str):
        """Invalidate caches related to topics."""
        # Invalidate user topics cache
        user_topics_key = cache_manager.get_cache_key("user_topics", user_id=user_id)
        await cache_manager.delete(user_topics_key)
        
        # Invalidate specific topic cache
        topic_key = cache_manager.get_cache_key("topic", topic_id=topic_id)
        await cache_manager.delete(topic_key)
        
        # Invalidate any list caches that might include this topic
        await cache_manager.invalidate_by_prefix(f"topics:{user_id}")

    @cached(key_prefix="topic", namespace="topics")
    async def get_topic(self, topic_id: str) -> Optional[Dict]:
        """
        Get topic metadata by ID with caching.
        
        Args:
            topic_id: ID of the topic to retrieve
            
        Returns:
            Dict containing topic metadata or None if not found
        """
        # This will only be called if not in cache
        topic = self.topics.get(topic_id)
        if topic:
            await cache_manager.set(
                cache_manager.get_cache_key("topic", topic_id=topic_id),
                topic
            )
        return topic

    async def get_message_topic(self, message_id: str) -> Optional[Dict]:
        """Get topic for a specific message."""
        topic_id = self._document_topics.get(message_id)
        if topic_id:
            return await self.get_topic(topic_id)
        return None

    @cached(key_prefix="user_topics", namespace="topics")
    async def get_user_topics(self, user_id: str) -> List[Dict]:
        """
        Get all topics for a user with caching.
        
        Args:
            user_id: ID of the user to get topics for
            
        Returns:
            List of topic dictionaries with metadata
        """
        # This will only be called if not in cache
        user_topics = [
            {"id": tid, **data} 
            for tid, data in self.topics.items() 
            if data.get("user_id") == user_id
        ]
        
        # Sort by last_updated (newest first)
        user_topics.sort(key=lambda x: x.get("last_updated", 0), reverse=True)
        
        return user_topics

    async def get_topic_messages(self, user_id: str, topic_id: str, limit: int = 50) -> List[Dict]:
        """
        Get messages for a specific topic with caching.
        
        Args:
            user_id: ID of the user
            topic_id: ID of the topic
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        cache_key = cache_manager.get_cache_key("topic_messages", 
                                             user_id=user_id, 
                                             topic_id=topic_id,
                                             limit=limit)
        
        cached_messages = await cache_manager.get(cache_key)
        if cached_messages is not None:
            return cached_messages
            
        # Get all user messages and filter by topic
        all_messages = await FirebaseService.get_messages(user_id=user_id, limit=1000)
        topic_messages = [
            msg for msg in all_messages 
            if msg.get("topic_id") == topic_id
        ][:limit]
        
        # Cache the result
        await cache_manager.set(cache_key, topic_messages)
        
        return topic_messages

# Create a singleton instance
topic_service = TopicService()
