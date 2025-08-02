from datetime import datetime, time
from zoneinfo import ZoneInfo
import exchange_calendars as xcals
from .config import Config

class MarketSchedule:
    """Manages US stock market schedule and checks if market is open."""
    
    def __init__(self):
        self.et_timezone = ZoneInfo('America/New_York')
        self.market_open = time(9, 30)  # 9:30 AM ET
        self.market_close = time(16, 0)  # 4:00 PM ET
        # 使用 XNYS (New York Stock Exchange) 日历
        self.calendar = xcals.get_calendar('XNYS')
        self.config = Config()
    
    def _get_current_et_time(self) -> datetime:
        """获取当前美东时间"""
        return datetime.now(self.et_timezone)
    
    def is_market_open(self) -> bool:
        """检查美股市场是否开市"""
        # 如果不需要在市场开放时间内查询，则始终返回True
        if not self.config.ONLY_QUERY_DURING_MARKET_HOURS:
            return True
            
        now = self._get_current_et_time()
        current_time = now.time()
        
        # 检查是否为交易日
        if not self.calendar.is_session(now.date()):
            return False
        
        # 检查是否在交易时间内
        return self.market_open <= current_time < self.market_close
