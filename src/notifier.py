"""
Notifier
Sends notifications to interested users about new vacancy posts
"""

import logging
import smtplib
from typing import Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """Handles notifications to users"""
    
    def __init__(self, config):
        """
        Initialize notifier
        
        Args:
            config: Configuration object with notification settings
        """
        self.config = config
        self.enabled = config.NOTIFICATIONS_ENABLED
        logger.info("Notifier initialized")
    
    def notify_users(self, post: Dict, analysis: Dict) -> bool:
        """
        Send notifications to subscribed users
        
        Args:
            post: The Facebook post
            analysis: Analysis results
        
        Returns:
            bool: True if notification sent successfully
        """
        if not self.enabled:
            logger.debug("Notifications are disabled")
            return False
        
        try:
            # Extract post information
            post_id = post.get('id', 'Unknown')
            post_text = post.get('message', post.get('story', 'No content'))
            post_url = post.get('permalink_url', '')
            created_time = post.get('created_time', datetime.now().isoformat())
            
            # Get users to notify
            users = self._get_subscribed_users()
            
            if not users:
                logger.warning("No subscribed users found")
                return False
            
            notification_data = {
                'post_id': post_id,
                'content': post_text,
                'url': post_url,
                'created_time': created_time,
                'matched_keywords': analysis.get('matched_keywords', []),
                'confidence': analysis.get('confidence', 0)
            }
            
            # Send via configured methods
            email_sent = self._send_email_notifications(users, notification_data)
            
            # Optional: SMS notifications
            if self.config.SMS_NOTIFICATIONS_ENABLED:
                self._send_sms_notifications(users, notification_data)
            
            # Optional: WhatsApp notifications
            if self.config.WHATSAPP_NOTIFICATIONS_ENABLED:
                self._send_whatsapp_notifications(users, notification_data)
            
            logger.info(f"Notifications sent for post {post_id}")
            return email_sent
        
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}", exc_info=True)
            return False
    
    def _get_subscribed_users(self) -> List[Dict]:
        """
        Get list of subscribed users
        
        Returns:
            List of user dictionaries with contact info
        """
        # This would typically fetch from database
        # For now, return from config
        return self.config.SUBSCRIBED_USERS
    
    def _send_email_notifications(self, users: List[Dict], notification_data: Dict) -> bool:
        """
        Send email notifications to users
        
        Args:
            users: List of users to notify
            notification_data: Notification content
        
        Returns:
            bool: True if successful
        """
        if not self.config.EMAIL_NOTIFICATIONS_ENABLED:
            logger.debug("Email notifications disabled")
            return False
        
        try:
            subject = f"🏠 New Broker-Free House Listing Found!"
            
            # Create message body
            body = self._create_email_body(notification_data)
            
            # Send to each user
            for user in users:
                if 'email' not in user:
                    continue
                
                try:
                    self._send_email(
                        to_email=user['email'],
                        subject=subject,
                        body=body
                    )
                    logger.info(f"Email sent to {user['email']}")
                except Exception as e:
                    logger.error(f"Failed to send email to {user['email']}: {str(e)}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error in email notification: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send a single email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body (HTML)
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.config.EMAIL_FROM
            message["To"] = to_email
            
            # Attach HTML content
            part = MIMEText(body, "html")
            message.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                server.sendmail(self.config.EMAIL_FROM, to_email, message.as_string())
            
            return True
        
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _create_email_body(self, notification_data: Dict) -> str:
        """
        Create HTML email body
        
        Args:
            notification_data: Notification details
        
        Returns:
            HTML string
        """
        keywords = ', '.join(notification_data['matched_keywords'])
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
                    <h2 style="color: #2c3e50;">🏠 New Housing Listing Found!</h2>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db;">
                        <h3>Post Details</h3>
                        <p><strong>Posted on:</strong> {notification_data['created_time']}</p>
                        <p><strong>Matched Keywords:</strong> {keywords}</p>
                        <p><strong>Confidence:</strong> {notification_data['confidence']:.0%}</p>
                        
                        <h3>Content Preview</h3>
                        <p style="background-color: #ecf0f1; padding: 15px; border-radius: 4px;">
                            {notification_data['content'][:500]}...
                        </p>
                        
                        <p>
                            <a href="{notification_data['url']}" 
                               style="display: inline-block; padding: 10px 20px; background-color: #3498db; 
                                      color: white; text-decoration: none; border-radius: 4px;">
                                View Full Post on Facebook
                            </a>
                        </p>
                    </div>
                    
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ecf0f1; font-size: 12px; color: #7f8c8d;">
                        <p>This is an automated notification from Facebook Housing Tracker.</p>
                        <p>You received this because you're subscribed to house vacancy alerts.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return html
    
    def _send_sms_notifications(self, users: List[Dict], notification_data: Dict) -> bool:
        """
        Send SMS notifications (placeholder)
        
        Args:
            users: List of users
            notification_data: Notification data
        
        Returns:
            bool: Success status
        """
        logger.info("SMS notifications not yet implemented")
        return False
    
    def _send_whatsapp_notifications(self, users: List[Dict], notification_data: Dict) -> bool:
        """
        Send WhatsApp notifications (placeholder)
        
        Args:
            users: List of users
            notification_data: Notification data
        
        Returns:
            bool: Success status
        """
        logger.info("WhatsApp notifications not yet implemented")
        return False
