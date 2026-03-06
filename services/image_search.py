import logging
import requests
import os
import hashlib
from typing import Optional

logger = logging.getLogger(__name__)

FALLBACK_WIKI_API = "https://en.wikipedia.org/w/api.php"


class WikipediaImageSearch:
    """Service for finding images on a MediaWiki-compatible wiki related to fantasy entities."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FantasyChatbot/1.0 (https://github.com/example/fantasy_chatbot; example@example.com)'
        })

    def get_image_url(self, entity_name: str, universe_name: str, wiki_api_base: Optional[str] = None) -> Optional[str]:
        """
        Search for an entity on the universe-specific wiki and return its main image URL.

        Args:
            entity_name: The name of the character, place, or event (e.g. "Aragorn")
            universe_name: The universe context for disambiguation (e.g. "Lord of the Rings")
            wiki_api_base: Base URL for the MediaWiki API to query. Falls back to
                           Wikipedia when None.

        Returns:
            URL to the original image, or None if not found
        """
        api_url = wiki_api_base or FALLBACK_WIKI_API
        wiki_label = api_url.split("//")[1].split("/")[0]  # e.g. "lotr.fandom.com"

        try:
            # Step 1: Search for the best matching article title
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": entity_name,
                "utf8": "",
                "format": "json",
                "srlimit": 1,
            }

            logger.info(f"Searching '{entity_name}' on {wiki_label}")
            search_response = self.session.get(api_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()

            if not search_data.get('query', {}).get('search'):
                logger.info(f"No article found for '{entity_name}' on {wiki_label}")
                return None

            article_title = search_data['query']['search'][0]['title']
            logger.info(f"Found article '{article_title}' on {wiki_label}")

            # Step 2: Fetch the main image for that article
            image_params = {
                "action": "query",
                "prop": "pageimages",
                "titles": article_title,
                "format": "json",
                "piprop": "original",
            }

            image_response = self.session.get(api_url, params=image_params, timeout=10)
            image_response.raise_for_status()
            image_data = image_response.json()

            pages = image_data.get('query', {}).get('pages', {})
            for page_id, page_info in pages.items():
                if 'original' in page_info and 'source' in page_info['original']:
                    img_url = page_info['original']['source']
                    logger.info(f"Retrieved image for '{article_title}' from {wiki_label}: {img_url}")
                    return img_url

            logger.info(f"No image found for article '{article_title}' on {wiki_label}")
            return None

        except requests.RequestException as e:
            logger.error(f"Error communicating with {wiki_label}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in image search on {wiki_label}: {e}")
            return None

    def download_image(self, url: str, save_dir: str) -> Optional[str]:
        """
        Download an image from a URL and save it to a local directory.

        Args:
            url: The URL of the image to download
            save_dir: The local directory to save the image to

        Returns:
            The filename of the saved image, or None if download failed
        """
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)

            # Generate a unique filename based on the URL hash
            # We also try to keep the original extension
            ext = os.path.splitext(url.split('?')[0])[-1]
            if not ext or len(ext) > 5:
                ext = ".jpg"  # Default to jpg if no clear extension

            url_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{url_hash}{ext}"
            filepath = os.path.join(save_dir, filename)

            # Check if file already exists to avoid re-downloading
            if os.path.exists(filepath):
                logger.debug(f"Image already exists: {filepath}")
                return filename

            # Download the image
            logger.info(f"Downloading image from {url} to {filepath}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded image: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None
