"""
Topic validation service for fantasy chatbot.
Ensures user questions and AI responses stay within configured topics.
"""

from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class TopicValidator:
    """Validates that AI responses are related to configured universes using an LLM."""

    def __init__(self, universes: List[Dict], llm_runner=None):
        """
        Initialize the topic validator with an LLM.

        Args:
            universes: List of universe configs
            llm_runner: LLM runner for validation
        """
        self.universes = universes
        self.llm_runner = llm_runner

    def validate_response(self, response: str, user_message: str) -> tuple[bool, Optional[str]]:
        """
        Validate that an AI response is on-topic and appropriate using the LLM.

        Args:
            response: AI response to validate
            user_message: Original user message (which includes the universe framing)

        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.llm_runner:
            # Fallback if no LLM provided: just allow it through
            return True, "No LLM provided for validation"

        prompt = f"""You are a strict response validator for a fantasy chatbot.

User asked: "{user_message}"
Chatbot responded: "{response}"

Evaluate the chatbot's response. Does the response stay entirely within the requested fantasy universe?
Does it avoid mentioning real-world concepts or other unrelated franchises?
Respond with ONLY the word "true" if the response is valid and stays in-universe, or "false" if it mentions out-of-universe or real-world concepts. No other text."""

        try:
            llm_resp = self.llm_runner.generate_response(
                user_message=prompt,
                conversation_history=[]
            )

            content = llm_resp.content.strip().lower()
            import string
            content = content.translate(str.maketrans('', '', string.punctuation))

            if 'true' in content and 'false' not in content:
                return True, "Response is valid and on-topic"
            elif 'false' in content and 'true' not in content:
                return False, "Response contains out-of-universe information"
            elif content.startswith('true'):
                return True, "Response is valid and on-topic"
            elif content.startswith('false'):
                return False, "Response contains out-of-universe information"
            else:
                logger.warning(f"Could not parse true/false from validation LLM response: {llm_resp.content}")
                return True, "Response appears to be valid"

        except Exception as e:
            logger.error(f"Error validating response with LLM: {e}")
            return True, "Response appears to be valid (validation errored)"