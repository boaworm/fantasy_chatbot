"""
Universe context service for fantasy chatbot.
Handles universe selection and query rewriting.
"""

from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel
from services.llm_runner import LLMRunner


logger = logging.getLogger(__name__)


class UniverseResource(BaseModel):
    """Model for a universe resource."""
    name: str
    description: Optional[str] = None


class Universe(BaseModel):
    """Model for a fantasy universe."""
    name: str
    keywords: List[str]


class UniverseContext:
    """Manages universe selection and query rewriting."""

    def __init__(self, universes: List[Dict[str, Any]], llm_runner: Optional[LLMRunner] = None):
        """
        Initialize the universe context manager.

        Args:
            universes: List of universe configurations
            llm_runner: Optional LLM runner for topic validation
        """
        self.universes = [Universe(**universe) for universe in universes]
        self.current_universe: Optional[Universe] = None
        self.llm_runner = llm_runner

    def get_universe_by_name(self, name: str) -> Optional[Universe]:
        """
        Get a universe by name.

        Args:
            name: Universe name

        Returns:
            Universe object or None
        """
        for universe in self.universes:
            if universe.name.lower() == name.lower():
                return universe
        return None

    def get_all_universe_names(self) -> List[str]:
        """
        Get list of all universe names.

        Returns:
            List of universe names
        """
        return [universe.name for universe in self.universes]

    def set_universe(self, name: str) -> bool:
        """
        Set the current universe.

        Args:
            name: Universe name

        Returns:
            True if universe found and set, False otherwise
        """
        universe = self.get_universe_by_name(name)
        if universe:
            self.current_universe = universe
            logger.info(f"Set universe to: {universe.name}")
            return True
        logger.warning(f"Universe not found: {name}")
        return False

    def get_current_universe(self) -> Optional[Universe]:
        """
        Get the current universe.

        Returns:
            Current universe or None
        """
        return self.current_universe

    def rewrite_query(self, query: str) -> str:
        """
        Rewrite query to include universe context.

        Args:
            query: Original user query

        Returns:
            Rewritten query with universe context
        """
        if not self.current_universe:
            return query

        # Try to include a relevant resource in the query
        # This is a simple approach - in production, you might want more sophisticated rewriting
        rewritten = f"{query} in {self.current_universe.name}"

        logger.info(f"Rewrote query: '{query}' -> '{rewritten}'")
        return rewritten

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the current universe.

        Returns:
            System prompt string
        """
        if self.current_universe:
            return f"You are a helpful assistant specializing in fantasy literature and role-playing games. Answer questions about {self.current_universe.name}."
        return "You are a helpful fantasy assistant."

    def get_resource_suggestions(self) -> List[str]:
        """
        Get resource suggestions for the current universe.

        Returns:
            List of resource names
        """
        if self.current_universe:
            return self.current_universe.keywords
        return []

    def validate_query_against_universe(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Validate that a query is related to the current universe using LLM.

        Args:
            query: Query to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.current_universe:
            return False, "No universe selected"

        # If LLM is available, use it to determine if the topic is related
        if self.llm_runner:
            try:
                is_related, reason = self._check_topic_with_llm(query)
                if is_related:
                    return True, reason
                return False, reason
            except Exception as e:
                logger.warning(f"LLM validation failed: {e}, falling back to keyword matching")

        # Fallback to keyword matching if LLM is not available
        query_lower = query.lower()

        # Check if query contains any universe keywords
        for keyword in self.current_universe.keywords:
            if keyword.lower() in query_lower:
                return True, f"Related to {self.current_universe.name}"

        # Check for universe name
        if self.current_universe.name.lower() in query_lower:
            return True, f"Related to {self.current_universe.name}"

        return False, f"Not related to {self.current_universe.name}"

    def _check_topic_with_llm(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Use LLM to check if a topic is related to the current universe.

        Args:
            query: Query to check

        Returns:
            Tuple of (is_related, reason)
        """
        universe_name = self.current_universe.name
        keywords = ", ".join(self.current_universe.keywords)

        prompt = f"""You are a topic validator for a fantasy chatbot. Your task is to determine if a user's question is related to a specific fantasy universe.

Current universe: {universe_name}
Universe keywords: {keywords}

User question: "{query}"

Analyze the question and determine:
1. Is this question related to the fantasy universe above?
2. Is this question, or any subject mentioned in it, commonly associated with the universe based on the keywords or general knowledge of the universe?
3. Is this a generic question that could apply to this universe (like "tell me about a big country")?

Return your answer in JSON format:
{{
    "is_related": true/false,
    "reason": "brief explanation (e.g., 'Yes, Aragorn is a character in Lord of the Rings' or 'No, this is a general question')",
    "is_generic": true/false
}}"""

        try:
            response = self.llm_runner.generate_response(
                user_message=prompt,
                conversation_history=[]
            )

            # Parse the response to extract JSON
            import json
            import re

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*"is_related"[^{}]*\}', response.content)
            if json_match:
                result = json.loads(json_match.group())
                return result["is_related"], result["reason"]
            else:
                # If we can't parse JSON, assume it's related
                logger.warning(f"Could not parse LLM response as JSON: {response.content}")
                return True, "Topic appears to be related"

        except Exception as e:
            logger.error(f"Error checking topic with LLM: {e}")
            return False, f"Error validating topic: {str(e)}"