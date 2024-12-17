from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import exchange_calendars as xcals
from typing import Tuple
from .config import Config

class MarketSchedule:
    """Manages US stock market schedule and checks if market is open."""
    
    def __init__(self):
        self.et_timezone = ZoneInfo('America/New_York')
        self.market_open = time(9, 30)  # 9:30 AM ET
        self.market_close = time(16, 0)  # 4:00 PM ET
        # 使用 XNYS (New York Stock Exchange) 日历
        self.calendar = xcals.get_calendar('XNYS')
    
    def _get_current_et_time(self) -> datetime:
        """获取当前美东时间"""
        return datetime.now(self.et_timezone)
    
    def is_market_open(self) -> bool:
        """检查美股市场是否开市"""
        # 如果不需要在市场开放时间内查询，则始终返回True
        if not Config.ONLY_QUERY_DURING_MARKET_HOURS:
            return True
            
        now = self._get_current_et_time()
        current_time = now.time()
        
        # 检查是否为交易日
        if not self.calendar.is_session(now.date()):
            return False
        
        # 检查是否在交易时间内
        return self.market_open <= current_time < self.market_close
    
    def next_open(self) -> datetime:
        """获取下一个交易日开市时间"""
        now = self._get_current_et_time()
        next_session = self.calendar.next_session(now.date())
        return self.calendar.session_open(next_session)
    
    def next_close(self) -> datetime:
        """获取当前交易日收市时间"""
        now = self._get_current_et_time()
        if not self.is_market_open():
            return now
        return self.calendar.session_close(now.date())
    
    def time_until_next_open(self) -> float:
        """获取距离下次开市的秒数"""
        if self.is_market_open():
            return 0
        now = self._get_current_et_time()
        next_open = self.next_open()
        return (next_open - now).total_seconds()
    
    def time_until_close(self) -> float:
        """获取距离收市的秒数"""
        if not self.is_market_open():
            return 0
        now = self._get_current_et_time()
        next_close = self.next_close()
        return (next_close - now).total_seconds()
    
    def get_beijing_time_range(self) -> Tuple[str, str]:
        """获取当前交易日对应的北京时间范围"""
        now = self._get_current_et_time()
        
        # 检查夏令时
        is_dst = bool(now.dst())
        
        if is_dst:
            open_time = "21:30"  # 美东9:30 = 北京21:30
            close_time = "04:00"  # 美东16:00 = 北京次日04:00
        else:
            open_time = "22:30"  # 美东9:30 = 北京22:30
            close_time = "05:00"  # 美东16:00 = 北京次日05:00
        
        return open_time, close_time
    
    def get_trading_schedule(self, date: datetime = None) -> dict:
        """获取指定日期的交易时间安排
        
        Returns:
            dict: 包含以下信息：
                - is_trading_day: 是否为交易日
                - market_open: 开市时间
                - market_close: 收市时间
                - next_trading_day: 下一个交易日
        """
        if date is None:
            date = self._get_current_et_time()
            
        schedule = {
            'is_trading_day': self.calendar.is_session(date.date()),
            'market_open': None,
            'market_close': None,
            'next_trading_day': None
        }
        
        if schedule['is_trading_day']:
            schedule['market_open'] = self.calendar.session_open(date.date())
            schedule['market_close'] = self.calendar.session_close(date.date())
        
        next_session = self.calendar.next_session(date.date())
        schedule['next_trading_day'] = self.calendar.session_open(next_session)
        
        return schedule
