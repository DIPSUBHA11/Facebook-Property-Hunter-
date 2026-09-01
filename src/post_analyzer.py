"""
Post Analyzer
Analyzes Facebook posts to detect housing vacancies and broker involvement
"""

import logging
import json
import re
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class PostAnalyzer:
    """Analyzes posts for vacancy and broker content"""
    
    def __init__(self, config):
        """
        Initialize analyzer with keywords
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.keywords = self._load_keywords()
        logger.info("Post analyzer initialized")
    
    def _load_keywords(self) -> Dict[str, List[str]]:
        """
        Load keywords from configuration file
        
        Returns:
            Dictionary with vacancy and exclude keywords
        """
        try:
            keywords_file = Path(__file__).parent.parent / 'config' / 'keywords.json'
            
            if keywords_file.exists():
                with open(keywords_file, 'r') as f:
                    keywords = json.load(f)
                logger.info("Keywords loaded from config file")
                return keywords
            else:
                logger.warning("Keywords file not found, using default keywords")
                return self._get_default_keywords()
        
        except Exception as e:
            logger.error(f"Error loading keywords: {str(e)}")
            return self._get_default_keywords()
    
    def _get_default_keywords(self) -> Dict[str, List[str]]:
        """
        Get default keywords if file not available
        
        Returns:
            Default keywords dictionary
        """
        return {
            "vacancy_keywords": [
                "vacant", "available", "rent", "sell", "house", "apartment",
                "flat", "property", "room", "space", "residential", "dwelling",
                "lease", "let", "for rent", "for sale", "looking for", "seeking",
                "open house", "viewing", "bhk", "studio", "bedroom"
            ],
            "exclude_keywords": [
                "broker", "agent", "realtor", "agency", "commission",
                "brokerage", "dealer", "intermediary", "through agent",
                "real estate", "representative", "property dealer",
                "contact agent", "listing agent", "registered agent"
            ],
            "additional_exclude": [
                "scam", "fake", "spam", "click bait"
            ]
        }
    
    def analyze(self, post: Dict) -> Dict:
        """
        Analyze a post for vacancy and broker content
        
        Args:
            post: Post dictionary from Facebook
        
        Returns:
            Dictionary with analysis results
        """
        # Extract text from post
        text = self._extract_text(post)
        
        if not text:
            return {
                'is_vacancy': False,
                'is_broker': False,
                'confidence': 0.0,
                'vacancy_score': 0.0,
                'broker_score': 0.0,
                'matched_keywords': [],
                'broker_keywords': []
            }
        
        # Convert to lowercase for analysis
        text_lower = text.lower()
        
        # Check for vacancy
        vacancy_matches = self._match_keywords(text_lower, self.keywords['vacancy_keywords'])
        vacancy_score = len(vacancy_matches) / max(len(self.keywords['vacancy_keywords']), 1)
        is_vacancy = len(vacancy_matches) > 0
        
        # Check for broker keywords
        broker_matches = self._match_keywords(text_lower, self.keywords['exclude_keywords'])
        
        # Additional exclusions
        additional_matches = self._match_keywords(text_lower, self.keywords.get('additional_exclude', []))
        
        all_exclude_matches = broker_matches + additional_matches
        broker_score = len(all_exclude_matches) / max(len(self.keywords['exclude_keywords']), 1)
        is_broker = len(all_exclude_matches) > 0
        
        # Calculate confidence
        confidence = self._calculate_confidence(is_vacancy, is_broker, vacancy_score, broker_score)
        
        result = {
            'is_vacancy': is_vacancy and not is_broker,
            'is_broker': is_broker,
            'confidence': confidence,
            'vacancy_score': vacancy_score,
            'broker_score': broker_score,
            'matched_keywords': vacancy_matches,
            'broker_keywords': all_exclude_matches
        }
        
        logger.debug(f"Post analysis: {result}")
        return result
    
    def _extract_text(self, post: Dict) -> str:
        """
        Extract all text content from a post
        
        Args:
            post: Post dictionary
        
        Returns:
            Combined text from post
        """
        text_parts = []
        
        # Extract various text fields
        if 'message' in post:
            text_parts.append(post['message'])
        if 'story' in post:
            text_parts.append(post['story'])
        if 'name' in post:
            text_parts.append(post['name'])
        
        return ' '.join(text_parts)
    
    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """
        Match keywords in text
        
        Args:
            text: Text to search
            keywords: List of keywords to match
        
        Returns:
            List of matched keywords
        """
        matched = []
        
        for keyword in keywords:
            # Use word boundaries for more accurate matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(keyword)
        
        return matched
    
    def _calculate_confidence(self, is_vacancy: bool, is_broker: bool,
                             vacancy_score: float, broker_score: float) -> float:
        """
        Calculate confidence score for the analysis
        
        Args:
            is_vacancy: Whether post is about vacancy
            is_broker: Whether post involves broker
            vacancy_score: Vacancy keyword match score
            broker_score: Broker keyword match score
        
        Returns:
            Confidence score (0-1)
        """
        if not is_vacancy:
            return 0.0
        
        if is_broker:
            return 0.0
        
        # Higher score for more keyword matches
        confidence = min(vacancy_score, 1.0)
        
        return confidence
    
    def filter_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Filter a list of posts for broker-free vacancies
        
        Args:
            posts: List of posts to filter
        
        Returns:
            Filtered list of valid vacancy posts
        """
        filtered = []
        
        for post in posts:
            analysis = self.analyze(post)
            if analysis['is_vacancy']:
                filtered.append({
                    'post': post,
                    'analysis': analysis
                })
        
        return filtered
