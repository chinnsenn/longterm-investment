"""Configuration management module."""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file

class Config:
    """Configuration management class."""
    
    def __init__(self):
        load_dotenv()
        self.retry_interval = int(os.getenv('RETRY_INTERVAL', '300'))
        
        # Paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DB_PATH = Path(os.getenv('DB_PATH', 'data/investment.db'))
        
        # Market Data Configuration
        self.MARKET_OPEN_HOUR = 9   # 市场开盘时间（小时）
        self.MARKET_OPEN_MINUTE = 30  # 市场开盘时间（分钟）
        self.MARKET_CLOSE_HOUR = 16   # 市场收盘时间（小时）
        self.MARKET_CLOSE_MINUTE = 0  # 市场收盘时间（分钟）
        
        # 数据更新间隔（秒）
        self.TRADING_UPDATE_INTERVAL = 600   # 交易时段每10分钟
        self.NON_TRADING_UPDATE_INTERVAL = 1800  # 非交易时段每30分钟
        
        # API Keys
        self.BARK_API_KEY = os.getenv('BARK_API_KEY', '')
        self.BARK_URL = os.getenv('BARK_URL', 'https://api.day.app')  # Bark server URL
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        
        # Market Data
        self.STOCK_SYMBOLS = ["QQQ", "SPY"]
        self.ONLY_QUERY_DURING_MARKET_HOURS = os.getenv('ONLY_QUERY_DURING_MARKET_HOURS', 'False').lower() == 'true'
        
        # Notification
        self.NOTIFICATION_COOLDOWN = int(os.getenv('NOTIFICATION_COOLDOWN', '3600'))  # seconds
        self.ERROR_RETRY_COUNT = int(os.getenv('ERROR_RETRY_COUNT', '3'))
    
    def get_update_interval(self) -> int:
        """
        根据当前时间确定更新间隔
        
        Returns:
            int: 更新间隔（秒）
                - 交易时间：600秒（10分钟）
                - 非交易时间且是交易日：3600秒（1小时）
                - 非交易日：86400秒（24小时）
        """
        current_time = datetime.now()
        
        # 检查是否是交易日（周一到周五）
        is_trading_day = current_time.weekday() < 5
        
        if not is_trading_day:
            # 非交易日，一天只需要更新一次
            return 86400  # 24小时
            
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
            return 600  # 交易时间：10分钟更新一次
        else:
            return 3600  # 非交易时间但是交易日：1小时更新一次
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    def validate(self):
        """Validate configuration."""
        if not self.BARK_API_KEY:
            raise ValueError("BARK_API_KEY is required")
            
        # Telegram configuration is optional, but both token and chat_id must be present if one is
        if bool(self.TELEGRAM_BOT_TOKEN) != bool(self.TELEGRAM_CHAT_ID):
            raise ValueError("Both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set if using Telegram")
