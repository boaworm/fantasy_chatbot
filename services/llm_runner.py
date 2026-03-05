"""
LLM runner service for fantasy chatbot.
Handles communication with OpenAI-compatible APIs.
"""

from typing import Optional, Dict, Any
from openai import OpenAI
import logging
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Model for LLM response."""
    content: str
    model: str
    finish_reason: str


class LLMRunner:
    """Handles LLM API communication."""

    def __init__(self, api_url: str, model: str, temperature: float = 0.7, max_tokens: int = 500, system_prompt: str = ""):
        """
        Initialize the LLM runner.

        Args:
            api_url: OpenAI-compatible API endpoint
            model: Model name
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            system_prompt: System prompt for the LLM
        """
        self.api_url = api_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

        # Initialize OpenAI client
        self.client = OpenAI(
            base_url=api_url,
            api_key="dummy"  # LM Studio doesn't require authentication
        )

    def generate_response(self, user_message: str, conversation_history: Optional[list] = None) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            user_message: User's message
            conversation_history: Optional list of previous messages

        Returns:
            LLMResponse object
        """
        try:
            # Build messages
            messages = []

            # Add system prompt
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)

            # Add current message
            messages.append({"role": "user", "content": user_message})

            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Extract response
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            logger.info(f"LLM response generated: {len(content)} characters")

            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=finish_reason
            )

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            raise

    def health_check(self) -> bool:
        """
        Check if the LLM API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to get model info
            models = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False