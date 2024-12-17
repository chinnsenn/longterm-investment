"""Notification module for sending alerts through multiple channels."""
import time
import logging
import requests
from urllib.parse import quote
from typing import Optional
from .config import Config

class Notifier:
    """Notification handler for sending alerts through multiple channels."""
    
    def __init__(self):
        """Initialize the notifier."""
        self._last_notification = 0
        self._retry_count = 0
        self._logger = logging.getLogger(__name__)
        self.config = Config()
        
        # 初始化日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _can_send_notification(self) -> bool:
        """Check if enough time has passed since the last notification."""
        current_time = time.time()
        if current_time - self._last_notification < self.config.NOTIFICATION_COOLDOWN:
            self._logger.info("Notification cooldown in effect")
            return False
        return True
    
    def _validate_config(self) -> bool:
        """Validate notification configuration."""
        if not hasattr(self.config, 'NOTIFICATION_COOLDOWN'):
            self._logger.error("NOTIFICATION_COOLDOWN not configured")
            return False
        if not hasattr(self.config, 'ERROR_RETRY_COUNT'):
            self._logger.error("ERROR_RETRY_COUNT not configured")
            return False
        if not hasattr(self.config, 'RETRY_INTERVAL'):
            self._logger.error("RETRY_INTERVAL not configured")
            return False
        return True
    
    def send_bark_notification(self, message: str, title: str = "Investment Alert") -> bool:
        """Send notification through Bark API."""
        if not hasattr(self.config, 'BARK_URL') or not hasattr(self.config, 'BARK_API_KEY'):
            self._logger.warning("Bark credentials not configured")
            return False
            
        try:
            # URL encode both title and body
            encoded_title = quote(title)
            encoded_body = quote(message)
            
            url = f"{self.config.BARK_URL}/{self.config.BARK_API_KEY}/{encoded_title}/{encoded_body}"
            self._logger.info(f"Sending Bark notification: {message} - {title}")
            
            response = requests.get(url, timeout=10)  # 添加超时设置
            response.raise_for_status()
            
            self._logger.info("Bark notification sent successfully")
            return True
            
        except requests.Timeout:
            self._logger.error("Bark notification timed out")
            return False
        except requests.RequestException as e:
            self._logger.error(f"Failed to send Bark notification: {str(e)}")
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error sending Bark notification: {str(e)}")
            return False
    
    def send_telegram_notification(self, message: str, title: str = "Investment Alert") -> bool:
        """Send notification through Telegram bot."""
        if not hasattr(self.config, 'TELEGRAM_BOT_TOKEN') or not hasattr(self.config, 'TELEGRAM_CHAT_ID'):
            self._logger.warning("Telegram credentials not configured")
            return False
            
        try:
            # Format message with title
            formatted_message = f"<b>{title}</b>\n\n{message}"
            
            url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
            self._logger.info(f"Sending Telegram notification: {title} - {message}")
            
            response = requests.post(
                url,
                json={
                    "chat_id": self.config.TELEGRAM_CHAT_ID,
                    "text": formatted_message,
                    "parse_mode": "HTML"
                },
                timeout=10  # 添加超时设置
            )
            response.raise_for_status()
            
            self._logger.info(f"Telegram API response: {response.json()}")
            return True
            
        except requests.Timeout:
            self._logger.error("Telegram notification timed out")
            return False
        except requests.RequestException as e:
            self._logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False
        except Exception as e:
            self._logger.error(f"Unexpected error sending Telegram notification: {str(e)}")
            return False
    
    def send_notification(self, message: str, title: str = "Investment Alert", retry: bool = True) -> bool:
        """Send notification through all available channels."""
        if not self._validate_config():
            return False
            
        if self._retry_count >= self.config.ERROR_RETRY_COUNT:
            self._logger.error("Max retry count reached, stopping notifications")
            return False
            
        if not self._can_send_notification():
            self._logger.info("Notification skipped due to cooldown")
            return False
            
        self._logger.info(f"Attempting to send notification: {message} - {title}")
        success = False
        
        # Try Bark
        bark_success = self.send_bark_notification(message, title)
        if bark_success:
            self._logger.info("Bark notification sent successfully")
        
        # Try Telegram
        telegram_success = self.send_telegram_notification(message, title)
        if telegram_success:
            self._logger.info("Telegram notification sent successfully")
        
        # Consider success if at least one channel worked
        success = bark_success or telegram_success
        
        if success:
            self._last_notification = time.time()
            self._retry_count = 0
            self._logger.info("Notification sent successfully through at least one channel")
        else:
            self._retry_count += 1
            self._logger.warning(f"Failed to send notification through any channel. Retry count: {self._retry_count}")
            if retry and self._retry_count < self.config.ERROR_RETRY_COUNT:
                self._logger.info(f"Retrying in {self.config.RETRY_INTERVAL} seconds...")
                time.sleep(self.config.RETRY_INTERVAL)
                return self.send_notification(message, title, retry=True)
            else:
                self._logger.error("All notification attempts failed")
        
        return success
