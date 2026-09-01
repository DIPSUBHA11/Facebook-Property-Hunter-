"""
Database Handler
Manages SQLite database for storing processed posts and user data
"""

import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Database:
    """Handles database operations"""
    
    def __init__(self, db_path: str = 'facebook_tracker.db'):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self._initialize()
        logger.info(f"Database initialized at {db_path}")
    
    def _initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            self._create_tables()
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create necessary database tables"""
        try:
            # Posts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    author TEXT,
                    created_time TIMESTAMP,
                    facebook_url TEXT,
                    vacancy_score REAL,
                    broker_score REAL,
                    is_broker INTEGER,
                    matched_keywords TEXT,
                    notified INTEGER DEFAULT 0,
                    processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(id)
                )
            ''')
            
            # Users table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    whatsapp TEXT,
                    active INTEGER DEFAULT 1,
                    subscribed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT
                )
            ''')
            
            # Notifications table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    user_id INTEGER,
                    notification_type TEXT,
                    sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Processed posts table (to avoid duplicates)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_posts (
                    id TEXT PRIMARY KEY,
                    processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def post_exists(self, post_id: str) -> bool:
        """
        Check if post has been processed
        
        Args:
            post_id: Facebook post ID
        
        Returns:
            bool: True if post exists in processed_posts
        """
        try:
            self.cursor.execute(
                'SELECT 1 FROM processed_posts WHERE id = ?',
                (post_id,)
            )
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking post existence: {str(e)}")
            return False
    
    def save_post(self, post: Dict, analysis: Dict) -> bool:
        """
        Save a vacancy post to database
        
        Args:
            post: Post dictionary from Facebook
            analysis: Analysis results
        
        Returns:
            bool: Success status
        """
        try:
            keywords_json = json.dumps(analysis.get('matched_keywords', []))
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO posts
                (id, content, created_time, facebook_url, vacancy_score, 
                 broker_score, is_broker, matched_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.get('id'),
                post.get('message', post.get('story', '')),
                post.get('created_time'),
                post.get('permalink_url', ''),
                analysis.get('vacancy_score', 0),
                analysis.get('broker_score', 0),
                1 if analysis.get('is_broker') else 0,
                keywords_json
            ))
            
            self.connection.commit()
            logger.info(f"Post {post.get('id')} saved to database")
            return True
        
        except Exception as e:
            logger.error(f"Error saving post: {str(e)}")
            return False
    
    def mark_processed(self, post_id: str) -> bool:
        """
        Mark a post as processed
        
        Args:
            post_id: Facebook post ID
        
        Returns:
            bool: Success status
        """
        try:
            self.cursor.execute(
                'INSERT OR IGNORE INTO processed_posts (id) VALUES (?)',
                (post_id,)
            )
            self.connection.commit()
            logger.debug(f"Post {post_id} marked as processed")
            return True
        
        except Exception as e:
            logger.error(f"Error marking post as processed: {str(e)}")
            return False
    
    def add_user(self, name: str, email: str, phone: str = None, 
                 whatsapp: str = None) -> Optional[int]:
        """
        Add a new user to the system
        
        Args:
            name: User name
            email: Email address
            phone: Phone number (optional)
            whatsapp: WhatsApp number (optional)
        
        Returns:
            User ID if successful, None otherwise
        """
        try:
            self.cursor.execute('''
                INSERT INTO users (name, email, phone, whatsapp)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, whatsapp))
            
            self.connection.commit()
            user_id = self.cursor.lastrowid
            logger.info(f"User {email} added with ID {user_id}")
            return user_id
        
        except sqlite3.IntegrityError:
            logger.warning(f"User {email} already exists")
            return None
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            return None
    
    def get_active_users(self) -> List[Dict]:
        """
        Get all active users
        
        Returns:
            List of user dictionaries
        """
        try:
            self.cursor.execute(
                'SELECT id, name, email, phone, whatsapp FROM users WHERE active = 1'
            )
            
            users = []
            for row in self.cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'whatsapp': row[4]
                })
            
            return users
        
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []
    
    def get_posts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get saved posts from database
        
        Args:
            limit: Maximum number of posts
            offset: Offset for pagination
        
        Returns:
            List of post dictionaries
        """
        try:
            self.cursor.execute('''
                SELECT id, content, created_time, facebook_url, 
                       vacancy_score, broker_score, matched_keywords
                FROM posts
                ORDER BY created_time DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            posts = []
            for row in self.cursor.fetchall():
                posts.append({
                    'id': row[0],
                    'content': row[1],
                    'created_time': row[2],
                    'facebook_url': row[3],
                    'vacancy_score': row[4],
                    'broker_score': row[5],
                    'matched_keywords': json.loads(row[6])
                })
            
            return posts
        
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return []
    
    def log_notification(self, post_id: str, user_id: int, 
                        notification_type: str, status: str = 'sent') -> bool:
        """
        Log a notification event
        
        Args:
            post_id: Facebook post ID
            user_id: User ID
            notification_type: Type of notification (email, sms, whatsapp)
            status: Notification status (sent, failed, pending)
        
        Returns:
            bool: Success status
        """
        try:
            self.cursor.execute('''
                INSERT INTO notifications
                (post_id, user_id, notification_type, status)
                VALUES (?, ?, ?, ?)
            ''', (post_id, user_id, notification_type, status))
            
            self.connection.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")
