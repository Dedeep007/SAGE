"""
AI Agent module using LangChain and Groq for intelligent responses.
Handles streaming responses, context management, and conversation flow.
"""
import asyncio
import logging
import time
from typing import AsyncGenerator, Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import json

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from config.settings import AI_CONFIG, GROQ_API_KEY, SYSTEM_MESSAGES
from src.screen_reader import ScreenContext

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Custom callback handler for streaming responses."""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated."""
        if self.callback:
            self.callback(token)
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts generating."""
        self.tokens = []
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating."""
        pass


class AIAgent:
    """
    Intelligent AI agent powered by LangChain and Groq.
    Handles conversation, context injection, and streaming responses.
    """
    
    def __init__(self):
        self.llm = None
        self.conversation_history: List[ConversationMessage] = []
        self.current_screen_context: Optional[ScreenContext] = None
        self.max_history = AI_CONFIG["max_context_history"]
        self.streaming_callback: Optional[Callable[[str], None]] = None
        
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Groq LLM with configuration."""
        try:
            if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
                raise ValueError("GROQ_API_KEY not properly configured")
            
            self.llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name=AI_CONFIG["model"],
                temperature=AI_CONFIG["temperature"],
                max_tokens=AI_CONFIG["max_tokens"],
                streaming=AI_CONFIG["streaming"],
            )
            
            logger.info(f"Initialized Groq LLM with model: {AI_CONFIG['model']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def set_streaming_callback(self, callback: Callable[[str], None]):
        """Set callback for streaming tokens."""
        self.streaming_callback = callback
    
    def update_screen_context(self, screen_context: ScreenContext):
        """Update current screen context for the agent."""
        self.current_screen_context = screen_context
        logger.debug(f"Updated screen context: {len(screen_context.text_content)} characters")
    
    async def process_message(self, user_message: str, include_screen_context: bool = True) -> AsyncGenerator[str, None]:
        """
        Process user message and generate streaming response.
        
        Args:
            user_message: User's input message
            include_screen_context: Whether to include current screen context
            
        Yields:
            Streaming tokens from the AI response
        """
        try:
            # Add user message to history
            self._add_to_history("user", user_message)
            
            # Prepare messages for the LLM
            messages = self._prepare_messages(include_screen_context)
            
            # Track response for history
            response_tokens = []
            
            # Set up temporary callback
            original_callback = self.streaming_callback
            
            try:
                # Generate streaming response (without callbacks - not supported by Groq)
                async for chunk in self.llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        # Debug: Print each token
                        logger.debug(f"AI token: '{chunk.content}'")
                        # Collect token for history
                        response_tokens.append(chunk.content)
                        yield chunk.content
                
                # Add complete response to history
                full_response = ''.join(response_tokens)
                # Fix unicode issues in logging
                try:
                    logger.info(f"AI complete response: {full_response[:100]}...")
                except UnicodeEncodeError:
                    logger.info(f"AI complete response: [Unicode content]")
                if full_response.strip():
                    self._add_to_history("assistant", full_response)
                
            finally:
                # Restore original callback
                self.streaming_callback = original_callback
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = "I apologize, but I encountered an error processing your request."
            yield error_msg
            self._add_to_history("assistant", error_msg)
    
    def _handle_token(self, token: str):
        """Handle individual tokens from streaming response."""
        if self.streaming_callback:
            self.streaming_callback(token)
    
    def _prepare_messages(self, include_screen_context: bool = True) -> List:
        """Prepare message list for the LLM including context and history."""
        messages = []
        
        # System message with persona
        system_content = SYSTEM_MESSAGES["assistant_persona"]
        
        # Add screen context if available and requested
        if include_screen_context and self.current_screen_context:
            screen_content = self.current_screen_context.text_content
            if screen_content.strip():
                context_prompt = SYSTEM_MESSAGES["screen_context_prompt"].format(
                    screen_content=screen_content[:2000]  # Limit context size
                )
                system_content += "\n\n" + context_prompt
        
        messages.append(SystemMessage(content=system_content))
        
        # Add conversation history (recent messages only)
        recent_history = self.conversation_history[-self.max_history:]
        
        for msg in recent_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        return messages
    
    def _add_to_history(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add message to conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        
        self.conversation_history.append(message)
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        logger.debug(f"Added {role} message to history: {len(content)} characters")
    
    def get_conversation_history(self) -> List[ConversationMessage]:
        """Get current conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    async def generate_proactive_suggestion(self) -> Optional[str]:
        """
        Generate proactive suggestion based on current screen context.
        
        Returns:
            Suggestion string or None if no suggestion available
        """
        if not self.current_screen_context or not self.current_screen_context.text_content.strip():
            return None
        
        try:
            suggestion_prompt = f"""Based on the current screen content, provide a brief, helpful suggestion or insight (max 50 words):

Screen content: {self.current_screen_context.text_content[:1000]}

Respond with a single, actionable suggestion or helpful observation. If the content doesn't warrant a suggestion, respond with "NO_SUGGESTION"."""
            
            messages = [
                SystemMessage(content="You are a helpful assistant providing brief, contextual suggestions."),
                HumanMessage(content=suggestion_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            suggestion = response.content.strip()
            
            if suggestion and suggestion != "NO_SUGGESTION" and len(suggestion) > 10:
                return suggestion
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestion: {e}")
            return None
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get current agent statistics."""
        return {
            "conversation_length": len(self.conversation_history),
            "has_screen_context": self.current_screen_context is not None,
            "screen_context_age": (
                time.time() - self.current_screen_context.timestamp 
                if self.current_screen_context else None
            ),
            "model": AI_CONFIG["model"],
            "streaming_enabled": AI_CONFIG["streaming"]
        }


# Singleton instance
_ai_agent_instance: Optional[AIAgent] = None


def get_ai_agent() -> AIAgent:
    """Get the global AI agent instance."""
    global _ai_agent_instance
    if _ai_agent_instance is None:
        _ai_agent_instance = AIAgent()
    return _ai_agent_instance
