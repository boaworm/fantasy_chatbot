"""
Topic validation service for fantasy chatbot.
Ensures user questions and AI responses stay within configured topics.
"""

from typing import List, Optional
from difflib import SequenceMatcher
import re


class TopicValidator:
    """Validates that text is related to configured topics."""

    def __init__(self, topics: List[str], threshold: float = 0.6, use_fuzzy: bool = True):
        """
        Initialize the topic validator.

        Args:
            topics: List of allowed topic strings
            threshold: Minimum similarity threshold (0.0-1.0)
            use_fuzzy: Whether to use fuzzy matching
        """
        self.topics = [topic.strip().lower() for topic in topics]
        self.threshold = threshold
        self.use_fuzzy = use_fuzzy

    def is_on_topic(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Check if text is related to any configured topic.

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_on_topic, reason)
        """
        if not text or not text.strip():
            return False, "Empty message"

        text_lower = text.strip().lower()

        # Check for exact topic matches
        for topic in self.topics:
            if topic in text_lower:
                return True, f"Related to: {topic.title()}"

        # Check for fuzzy matches
        if self.use_fuzzy:
            for topic in self.topics:
                similarity = self._calculate_similarity(text_lower, topic)
                if similarity >= self.threshold:
                    return True, f"Related to: {topic.title()} (similarity: {similarity:.2f})"

        return False, "Not related to configured topics"

    def _calculate_similarity(self, text: str, topic: str) -> float:
        """
        Calculate similarity between text and topic using sequence matching.

        Args:
            text: Text to compare
            topic: Topic to compare against

        Returns:
            Similarity score (0.0-1.0)
        """
        # Try to find common words
        text_words = set(re.findall(r'\b\w+\b', text))
        topic_words = set(re.findall(r'\b\w+\b', topic))

        # Calculate Jaccard similarity
        intersection = text_words & topic_words
        union = text_words | topic_words

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def validate_response(self, response: str, user_message: str) -> tuple[bool, Optional[str]]:
        """
        Validate that an AI response is on-topic.

        Args:
            response: AI response to validate
            user_message: Original user message

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check if response is on-topic
        is_on_topic, reason = self.is_on_topic(response)

        if not is_on_topic:
            return False, f"Response is off-topic: {reason}"

        # Check if response is directly related to user's question
        response_lower = response.lower()
        user_lower = user_message.lower()

        # Ensure response addresses the user's question
        if len(response_lower) < 10:
            return False, "Response is too short to be meaningful"

        # Check for conversational filler
        filler_words = {"um", "uh", "ah", "like", "you know"}
        if any(word in response_lower for word in filler_words):
            return False, "Response contains conversational filler"

        return True, "Response is valid and on-topic"