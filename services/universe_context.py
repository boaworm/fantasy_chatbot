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
            The answer may only contain places, names, characters and events from the selected universe.
            If the question is generic, such as "What is a dragon?", the answer may include information about dragons from this universet
            If the question is generic, such as "Tell me about a famous character", the answer may include information about a famous character from this universe, but not a generic character that is not related to the universe.      
                
          """
        if not self.current_universe:
            return query

        rewritten = f"""{query}

(Please answer this question strictly from the perspective of the {self.current_universe.name} universe.
Your answer may only contain places, names, characters and events from {self.current_universe.name}.
If the question is generic, such as "What is a dragon?" or "Tell me about a famous character", provide an answer based entirely on the lore of {self.current_universe.name} and do not reference generic concepts from outside this universe.)"""

        log_friendly = rewritten.replace('\n', ' ')
        logger.info(f"Rewrote query: '{query}' -> '{log_friendly}'")
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

    def validate_query_against_universe(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> tuple[bool, Optional[str]]:
        """
        Validate that a query is related to the current universe using LLM.

        Args:
            query: Query to validate
            history: Optional conversation history to provide context for pronouns

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.current_universe:
            return False, "No universe selected"

        # If LLM is available, use it to determine if the topic is related
        if self.llm_runner:
            try:
                is_related, reason = self._check_topic_with_llm(query, history)
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

    def _check_topic_with_llm(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> tuple[bool, Optional[str]]:
        """
        Use LLM to check if a topic is related to the current universe.

        Args:
            query: Query to check
            history: Optional conversation history to provide context

        Returns:
            Tuple of (is_related, reason)
        """
        universe_name = self.current_universe.name
        keywords = ", ".join(self.current_universe.keywords)

        # Build context string from history if provided (last 2 turns typically sufficient)
        context_str = ""
        if history and len(history) > 0:
            context_str = "\nPrevious Conversation Context (for resolving pronouns like 'he' or 'it'):\n"
            # Get up to the last 2 messages for immediate context
            recent_history = history[-2:]
            for msg in recent_history:
                role = "User" if msg.get("role") == "user" else "Chatbot"
                # Truncate very long responses so as not to confuse the validator
                content = msg.get("content", "")
                if len(content) > 300:
                    content = content[:300] + "..."
                context_str += f"{role}: {content}\n"

        prompt = f"""You are a strict topic validator for a fantasy chatbot. Your task is to determine if a user's question can be answered within the context of the selected fantasy universe.

Current universe: {universe_name}
Universe keywords: {keywords}
{context_str}
User question: "{query}"

Does the user question make sense to answer from the perspective of the {universe_name} universe?
Can the question be answered using the lore, characters, places, or rules of this universe?
(If the question uses pronouns like "he" or "it", use the provided conversation context to understand what it refers to).
Respond with ONLY the word "true" if it can be answered, or "false" if it cannot. No other text, no explanation, no punctuation, and no JSON formatting.

Examples:
Universe: Lord of the Rings
Question: "Who is the Dark Lord?"
Response: true

Universe: Lord of the Rings
Question: "What is the capital of France?"
Response: false

Universe: Belgariad
Question: "Who is the main antagonist?"
Response: true

Universe: Belgariad
Question: "What is the tallest mountain on Earth?"
Response: false

Universe: Lord of the Rings
Question: "Tell me about the Green Dragon inv."
Response: true

Universe: Lord of the Rings
Question: "Tell me about a famous green dragon."
Response: false

Universe: Dungeons & Dragons
Question: "Tell me about a famous green dragon."
Response: true"""

        try:
            response = self.llm_runner.generate_response(
                user_message=prompt,
                conversation_history=[]
            )

            content = response.content.strip().lower()
            
            # Remove any trailing punctuation just in case
            import string
            content = content.translate(str.maketrans('', '', string.punctuation))

            if 'true' in content and 'false' not in content:
                return True, "Topic is related to the universe"
            elif 'false' in content and 'true' not in content:
                return False, "Topic is not related to the universe"
            elif content.startswith('true'):
                return True, "Topic is related to the universe"
            elif content.startswith('false'):
                return False, "Topic is not related to the universe"
            else:
                logger.warning(f"Could not parse true/false from LLM response: {response.content}")
                return True, "Topic appears to be related"

        except Exception as e:
            logger.error(f"Error checking topic with LLM: {e}")
            # For any other error, assume it's related to avoid false negatives
            return True, "Topic appears to be related"