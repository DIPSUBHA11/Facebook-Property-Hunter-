"""
Facebook Housing Tracker - Main Application
Monitors Facebook posts for house vacancy listings and notifies interested parties
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.facebook_handler import FacebookHandler
from src.post_analyzer import PostAnalyzer
from src.notifier import Notifier
from src.database import Database
from config.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('facebook_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FacebookHousingTracker:
    """Main application class for tracking Facebook housing posts"""
    
    def __init__(self):
        """Initialize the tracker with all components"""
        self.config = Config()
        self.db = Database()
        self.facebook = FacebookHandler(self.config)
        self.analyzer = PostAnalyzer(self.config)
        self.notifier = Notifier(self.config)
        logger.info("Facebook Housing Tracker initialized")
    
    def process_posts(self):
        """
        Main processing loop:
        1. Fetch posts from Facebook
        2. Analyze for vacancy
        3. Filter broker posts
        4. Notify interested parties
        """
        try:
            logger.info("Starting post processing...")
            
            # Fetch posts from configured sources
            posts = self.facebook.fetch_posts()
            logger.info(f"Fetched {len(posts)} posts from Facebook")
            
            if not posts:
                logger.warning("No posts retrieved from Facebook")
                return
            
            processed_count = 0
            
            for post in posts:
                # Skip if already processed
                if self.db.post_exists(post['id']):
                    logger.debug(f"Post {post['id']} already processed, skipping")
                    continue
                
                # Analyze post content
                analysis = self.analyzer.analyze(post)
                
                if analysis['is_vacancy']:
                    logger.info(f"Vacancy detected in post {post['id']}")
                    
                    # Check if it's not a broker post
                    if not analysis['is_broker']:
                        logger.info(f"Post {post['id']} is broker-free, adding to database")
                        
                        # Store in database
                        self.db.save_post(post, analysis)
                        
                        # Send notifications
                        self.notifier.notify_users(post, analysis)
                        processed_count += 1
                    else:
                        logger.info(f"Post {post['id']} is broker-related, skipping")
                
                # Mark post as processed
                self.db.mark_processed(post['id'])
            
            logger.info(f"Processing complete. {processed_count} vacancy posts found")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error during post processing: {str(e)}", exc_info=True)
            return 0
    
    def run_continuous(self, interval_minutes=30):
        """
        Run the tracker continuously
        
        Args:
            interval_minutes: Time between checks (default: 30 minutes)
        """
        logger.info(f"Starting continuous tracking with {interval_minutes} minute intervals")
        
        try:
            while True:
                start_time = datetime.now()
                logger.info(f"Running scan at {start_time}")
                
                self.process_posts()
                
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, (interval_minutes * 60) - elapsed)
                
                if sleep_time > 0:
                    logger.info(f"Sleeping for {sleep_time:.0f} seconds until next scan")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Tracking stopped by user")
        except Exception as e:
            logger.error(f"Fatal error in continuous tracking: {str(e)}", exc_info=True)
    
    def run_once(self):
        """Run a single scan and exit"""
        logger.info("Running single scan")
        return self.process_posts()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")
        self.db.close()
        logger.info("Cleanup complete")


def main():
    """Application entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Housing Tracker')
    parser.add_argument('--once', action='store_true', help='Run single scan and exit')
    parser.add_argument('--interval', type=int, default=30, help='Interval in minutes for continuous mode')
    
    args = parser.parse_args()
    
    tracker = FacebookHousingTracker()
    
    try:
        if args.once:
            tracker.run_once()
        else:
            tracker.run_continuous(args.interval)
    finally:
        tracker.cleanup()


if __name__ == '__main__':
    main()
