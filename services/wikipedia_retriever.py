"""
Wikipedia retriever service for Earth universe.
Handles fetching article data from Wikipedia API.
"""

import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WikipediaRetriever:
    """Service for fetching and processing Wikipedia articles."""

    def __init__(self):
        """Initialize the Wikipedia retriever."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FantasyChatbot/1.0 (Earth Universe; fantasy_chatbot@example.com)'
        })
        self.search_api = "https://en.wikipedia.org/w/api.php"
        self.summary_api = "https://en.wikipedia.org/api/rest_v1/page/summary"

    def search_articles(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for articles matching the query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search result dictionaries with title, snippet, etc.
        """
        try:
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "utf8": ""
            }

            logger.info(f"Searching Wikipedia for: '{query}'")
            response = self.session.get(self.search_api, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = data.get('query', {}).get('search', [])
            logger.info(f"Found {len(results)} search results")

            return results

        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []

    def fetch_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a summary for a Wikipedia article.

        Args:
            title: Article title

        Returns:
            Article summary dictionary or None
        """
        try:
            url = f"{self.summary_api}/{title}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if it's a disambiguation page or redirect
            if data.get('type') in ['disambiguation', 'redirection']:
                logger.info(f"Skipping {data.get('type')} page: {title}")
                return None

            return data

        except Exception as e:
            logger.error(f"Error fetching summary for '{title}': {e}")
            return None

    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract plain text from HTML content.

        Args:
            html_content: HTML string

        Returns:
            Plain text string
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for tag in soup(['script', 'style', 'sup', 'ref']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            # Clean up multiple spaces
            text = ' '.join(text.split())
            return text
        except Exception as e:
            logger.warning(f"Error parsing HTML: {e}")
            return html_content

    def search_and_fetch(self, query: str, max_articles: int = 2) -> List[Dict[str, Any]]:
        """
        Search Wikipedia and fetch full summaries for top results.

        Args:
            query: Search query
            max_articles: Maximum articles to fetch

        Returns:
            List of article dictionaries with title, extract, thumbnail, etc.
        """
        # Step 1: Search for articles
        search_results = self.search_articles(query, max_results=max_articles * 2)

        if not search_results:
            logger.warning(f"No search results for: '{query}'")
            return []

        # Step 2: Fetch summaries for top results
        articles = []
        for result in search_results[:max_articles * 2]:
            title = result.get('title')
            if not title:
                continue

            summary = self.fetch_summary(title)
            if summary and summary.get('type') not in ['disambiguation']:
                articles.append(summary)
                if len(articles) >= max_articles:
                    break

        logger.info(f"Fetched {len(articles)} Wikipedia articles")
        return articles

    def join_articles(self, articles: List[Dict[str, Any]]) -> Tuple[str, List[Tuple[str, Optional[str]]]]:
        """
        Join multiple articles into a single context string and extract entity images.

        Args:
            articles: List of article dictionaries from Wikipedia

        Returns:
            Tuple of (combined_text, entity_images)
            where entity_images is a list of (entity_name, image_url) tuples
        """
        if not articles:
            return ("", [])

        combined_text_parts = []
        entity_images = []

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown')
            extract = article.get('extract', '')
            thumbnail = article.get('thumbnail', {})
            image_url = thumbnail.get('source') if thumbnail else None

            # Add article content
            article_text = f"""
=== {title} ===

{extract}

"""
            combined_text_parts.append(article_text)

            # Add entity-image pair for image search
            entity_images.append((title, image_url))

            logger.info(f"Article {i}: '{title}' - Extract length: {len(extract)} chars, Image: {image_url is not None}")

        combined_text = "\n".join(combined_text_parts)

        return (combined_text, entity_images)

    def get_image_url_for_entity(self, entity_name: str) -> Optional[str]:
        """
        Get the main image URL for a specific entity/article.

        Args:
            entity_name: Name of the entity/article

        Returns:
            Image URL or None
        """
        summary = self.fetch_summary(entity_name)
        if summary:
            thumbnail = summary.get('thumbnail', {})
            return thumbnail.get('source') if thumbnail else None
        return None
