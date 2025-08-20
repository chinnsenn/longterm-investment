"""Configuration management module."""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from .constants import (
    RETRY_INTERVAL,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    TRADING_UPDATE_INTERVAL,
    NON_TRADING_UPDATE_INTERVAL,
    HOURLY_UPDATE_INTERVAL,
    DAILY_UPDATE_INTERVAL,
    DEFAULT_NOTIFICATION_COOLDOWN,
    DEFAULT_ERROR_RETRY_COUNT
)

# Load environment variables from .env file

class Config:
    """Configuration management class."""
    
    def __init__(self):
        load_dotenv()
        self.RETRY_INTERVAL = int(os.getenv('RETRY_INTERVAL', str(RETRY_INTERVAL)))
        
        # Paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DB_PATH = Path(os.getenv('DB_PATH', 'data/investment.db'))
        
        # Market Data Configuration
        self.MARKET_OPEN_HOUR = MARKET_OPEN_HOUR
        self.MARKET_OPEN_MINUTE = MARKET_OPEN_MINUTE
        self.MARKET_CLOSE_HOUR = MARKET_CLOSE_HOUR
        self.MARKET_CLOSE_MINUTE = MARKET_CLOSE_MINUTE
        
        # Data update intervals (seconds)
        self.TRADING_UPDATE_INTERVAL = TRADING_UPDATE_INTERVAL
        self.NON_TRADING_UPDATE_INTERVAL = NON_TRADING_UPDATE_INTERVAL
        
        # API Keys
        self.BARK_API_KEY = os.getenv('BARK_API_KEY', '')
        self.BARK_URL = os.getenv('BARK_URL', 'https://api.day.app')  # Bark server URL
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        
        # Market Data
        self.STOCK_SYMBOLS = ["QQQ", "SPY"]
        self.ONLY_QUERY_DURING_MARKET_HOURS = os.getenv('ONLY_QUERY_DURING_MARKET_HOURS', 'False').lower() == 'true'
        
        # Notification
        self.NOTIFICATION_COOLDOWN = int(os.getenv('NOTIFICATION_COOLDOWN', str(DEFAULT_NOTIFICATION_COOLDOWN)))  # seconds
        self.ERROR_RETRY_COUNT = int(os.getenv('ERROR_RETRY_COUNT', str(DEFAULT_ERROR_RETRY_COUNT)))
    
    def get_update_interval(self) -> int:
        """
        根据当前时间确定更新间隔
        
        Returns:
            int: 更新间隔（秒）
                - 交易时间：600秒（10分钟）
                - 非交易时间且是交易日：3600秒（1小时）
                - 非交易日：86400秒（24小时）
                - 如果 ONLY_QUERY_DURING_MARKET_HOURS 为 False：3600秒（1小时）
        """
        # 如果不限制只在交易时间查询，统一使用1小时间隔
        if not self.ONLY_QUERY_DURING_MARKET_HOURS:
            return HOURLY_UPDATE_INTERVAL  # 1小时更新一次
            
        current_time = datetime.now()
        
        # 检查是否是交易日（周一到周五）
        is_trading_day = current_time.weekday() < 5
        
        if not is_trading_day:
            # 非交易日，一天只需要更新一次
            return DAILY_UPDATE_INTERVAL  # 24小时
            
        # 美股交易时间：9:30 - 16:00 (EST)
        # 转换为北京时间：21:30 - 04:00
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # 判断是否在交易时间
        # 21:30 - 23:59 或 00:00 - 04:00
        is_trading_hours = (
            (current_hour == 21 and current_minute >= 30) or
            (current_hour >= 22 and current_hour <= 23) or
            (current_hour >= 0 and current_hour < 4)
        )
        
        if is_trading_hours:
            return TRADING_UPDATE_INTERVAL  # 交易时间：10分钟更新一次
        else:
            return HOURLY_UPDATE_INTERVAL  # 非交易时间但是交易日：1小时更新一次
    
    def ensure_directories(self):
        """Ensure all required directories exist with proper permissions."""
        try:
            # Create parent directories if they don't exist
            self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to set proper permissions (755) for the data directory
            # This helps avoid permission issues in different environments
            import stat
            self.DB_PATH.parent.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        except Exception as e:
            # Log the error but don't fail - the app might still work if permissions are adequate
            import logging
            logging.warning(f"Could not set permissions on data directory {self.DB_PATH.parent}: {e}")
            logging.warning("This may cause database access issues. Please ensure the directory is writable by the application.")
            
        # Additional check for VPS environments
        try:
            # Test if we can write to the directory
            test_file = self.DB_PATH.parent / ".permission_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            import logging
            logging.error(f"Permission test failed for {self.DB_PATH.parent}: {e}")
            logging.error("This indicates a permission issue that may prevent the application from running properly.")
            logging.error("For VPS deployments, try running with: UID=$(id -u) GID=$(id -g) docker compose up -d")
    
    def validate(self):
        """Validate configuration."""
        if not self.BARK_API_KEY:
            raise ValueError("BARK_API_KEY is required")
            
        # Telegram configuration is optional, but both token and chat_id must be present if one is
        if bool(self.TELEGRAM_BOT_TOKEN) != bool(self.TELEGRAM_CHAT_ID):
            raise ValueError("Both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set if using Telegram")
