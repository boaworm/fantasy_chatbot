import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class WikipediaImageSearch:
    """Service for finding images on Wikipedia related to fantasy entities."""

    def __init__(self):
        self.session = requests.Session()
        # A good practice for Wikipedia API is to set a User-Agent
        self.session.headers.update({
            'User-Agent': 'FantasyChatbot/1.0 (https://github.com/example/fantasy_chatbot; example@example.com)'
        })

    def get_image_url(self, entity_name: str, universe_name: str) -> Optional[str]:
        """
        Search for an entity in the context of a universe and return its main Wikipedia image URL.
        
        Args:
            entity_name: The name of the character, place, or event (e.g. "Aragorn")
            universe_name: The universe context for disambiguation (e.g. "Lord of the Rings")
            
        Returns:
            URL to the original image, or None if not found
        """
        try:
            # Step 1: Search to find the exact Wikipedia article title
            # Including universe name helps resolve ambiguity (e.g. "Aragorn Lord of the Rings")
            search_query = f"{entity_name} {universe_name}"
            search_url = "https://en.wikipedia.org/w/api.php"
            
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": search_query,
                "utf8": "",
                "format": "json",
                "srlimit": 1
            }
            
            search_response = self.session.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get('query', {}).get('search'):
                logger.info(f"No Wikipedia article found for '{search_query}'")
                return None
                
            article_title = search_data['query']['search'][0]['title']
            logger.info(f"Found Wikipedia article: '{article_title}' for entity '{entity_name}'")
            
            # Step 2: Get the original image (pageimage) for that specific title
            image_params = {
                "action": "query",
                "prop": "pageimages",
                "titles": article_title,
                "format": "json",
                "piprop": "original"
            }
            
            image_response = self.session.get(search_url, params=image_params)
            image_response.raise_for_status()
            image_data = image_response.json()
            
            pages = image_data.get('query', {}).get('pages', {})
            for page_id, page_info in pages.items():
                if 'original' in page_info and 'source' in page_info['original']:
                    img_url = page_info['original']['source']
                    logger.info(f"Successfully retrieved image for '{article_title}': {img_url}")
                    return img_url
                    
            logger.info(f"No original image found for article '{article_title}'")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error communicating with Wikipedia API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Wikipedia image search: {e}")
            return None
