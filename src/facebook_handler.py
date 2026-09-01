"""
Facebook API Handler
Manages authentication and post fetching from Facebook
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FacebookHandler:
    """Handles Facebook API interactions"""
    
    def __init__(self, config):
        """
        Initialize Facebook handler
        
        Args:
            config: Configuration object with Facebook credentials
        """
        self.config = config
        self.access_token = config.FACEBOOK_ACCESS_TOKEN
        self.graph_api_version = config.FACEBOOK_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        self.session = requests.Session()
        logger.info("Facebook handler initialized")
    
    def authenticate(self) -> bool:
        """
        Verify Facebook API authentication
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            url = f"{self.base_url}/me"
            params = {'access_token': self.access_token}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info("Facebook authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def fetch_posts(self, sources: Optional[List[str]] = None) -> List[Dict]:
        """
        Fetch posts from specified Facebook groups or pages
        
        Args:
            sources: List of group/page IDs to fetch from (uses config if None)
        
        Returns:
            List of post dictionaries
        """
        if sources is None:
            sources = self.config.FACEBOOK_SOURCES
        
        all_posts = []
        
        for source_id in sources:
            try:
                logger.info(f"Fetching posts from source: {source_id}")
                posts = self._fetch_from_source(source_id)
                all_posts.extend(posts)
                logger.info(f"Retrieved {len(posts)} posts from {source_id}")
            except Exception as e:
                logger.error(f"Error fetching from {source_id}: {str(e)}")
                continue
        
        return all_posts
    
    def _fetch_from_source(self, source_id: str) -> List[Dict]:
        """
        Fetch posts from a single source
        
        Args:
            source_id: Facebook group or page ID
        
        Returns:
            List of posts
        """
        posts = []
        
        try:
            # Fetch feed from the source
            url = f"{self.base_url}/{source_id}/feed"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,story,created_time,link,type,name,picture,permalink_url',
                'limit': 100
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', [])
                logger.info(f"Successfully fetched feed from {source_id}")
            else:
                logger.error(f"Feed fetch failed for {source_id}: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error in _fetch_from_source: {str(e)}")
        
        return posts
    
    def get_post_details(self, post_id: str) -> Dict:
        """
        Get detailed information about a specific post
        
        Args:
            post_id: Facebook post ID
        
        Returns:
            Dictionary with post details
        """
        try:
            url = f"{self.base_url}/{post_id}"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,story,created_time,link,type,name,picture,comments.limit(10),likes.summary(total_count)'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get post details: {response.status_code}")
                return {}
        
        except Exception as e:
            logger.error(f"Error getting post details: {str(e)}")
            return {}
    
    def get_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        """
        Get comments from a post
        
        Args:
            post_id: Facebook post ID
            limit: Maximum number of comments to fetch
        
        Returns:
            List of comments
        """
        try:
            url = f"{self.base_url}/{post_id}/comments"
            params = {
                'access_token': self.access_token,
                'fields': 'id,message,created_time,from',
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                logger.error(f"Failed to get comments: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return []
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.info("Facebook handler session closed")
