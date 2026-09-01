"""
Configuration Settings
Centralized configuration for the Facebook Housing Tracker
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class"""
    
    # ===== FACEBOOK API SETTINGS =====
    FACEBOOK_ACCESS_TOKEN = os.getenv(
        'FACEBOOK_ACCESS_TOKEN',
        'YOUR_FACEBOOK_ACCESS_TOKEN_HERE'
    )
    FACEBOOK_API_VERSION = os.getenv('FACEBOOK_API_VERSION', 'v18.0')
    
    # Facebook sources to monitor (group/page IDs)
    # Add your Facebook group or page IDs here
    FACEBOOK_SOURCES = os.getenv(
        'FACEBOOK_SOURCES',
        '123456789,987654321'
    ).split(',')
    
    # ===== NOTIFICATION SETTINGS =====
    NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'True') == 'True'
    
    # Email notifications
    EMAIL_NOTIFICATIONS_ENABLED = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'True') == 'True'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True') == 'True'
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'your_email@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_app_password')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'facebook-tracker@yourdomain.com')
    
    # SMS notifications (optional)
    SMS_NOTIFICATIONS_ENABLED = os.getenv('SMS_NOTIFICATIONS_ENABLED', 'False') == 'True'
    SMS_API_KEY = os.getenv('SMS_API_KEY', '')
    SMS_SERVICE = os.getenv('SMS_SERVICE', 'twilio')  # twilio, AWS SNS, etc.
    
    # WhatsApp notifications (optional)
    WHATSAPP_NOTIFICATIONS_ENABLED = os.getenv('WHATSAPP_NOTIFICATIONS_ENABLED', 'False') == 'True'
    WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN', '')
    
    # ===== USER PREFERENCES =====
    # Subscribed users for notifications
    SUBSCRIBED_USERS = [
        {
            'name': 'User 1',
            'email': 'user1@example.com',
            'phone': '+91XXXXXXXXXX',
            'whatsapp': '+91XXXXXXXXXX'
        },
        {
            'name': 'User 2',
            'email': 'user2@example.com',
            'phone': '+91XXXXXXXXXX',
            'whatsapp': '+91XXXXXXXXXX'
        }
    ]
    
    # ===== ANALYSIS SETTINGS =====
    # Minimum confidence score to send notification (0-1)
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.3'))
    
    # ===== TRACKING SETTINGS =====
    # How often to check for new posts (in minutes)
    CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '30'))
    
    # Maximum posts to fetch per check
    MAX_POSTS_PER_CHECK = int(os.getenv('MAX_POSTS_PER_CHECK', '100'))
    
    # ===== DATABASE SETTINGS =====
    DATABASE_PATH = os.getenv('DATABASE_PATH', './facebook_tracker.db')
    
    # ===== LOGGING SETTINGS =====
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './facebook_tracker.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    NOTIFICATIONS_ENABLED = False
    DATABASE_PATH = ':memory:'


def get_config(env=None):
    """
    Get configuration based on environment
    
    Args:
        env: Environment name (development, production, testing)
    
    Returns:
        Config object
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(env, DevelopmentConfig)()
