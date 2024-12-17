from typing import List, Tuple, Optional
from .database import DatabaseManager
from .market_data import MarketData
from .notification import Notifier

class RatioCalculator:
    def __init__(self, market_data: MarketData):
        self.market_data = market_data

class QQQSPYRatioCalculator:
    """
    QQQ/SPY ratio calculator implementing the following strategy rules:
    
    1. Strategy switching rules:
       - Can only switch between CASH and QQQ (1-3)
       - Can only switch between CASH and SPY (2-3)
       - Cannot directly switch between QQQ and SPY
       - Must sell current position before switching to new position
    
    2. Entry conditions:
       - For QQQ: When N > V (ratio above threshold)
       - For SPY: When N ≤ V AND SPY > 40-week MA
    
    3. Exit conditions:
       - For QQQ: When N ≤ V
       - For SPY: When N > V OR SPY ≤ 40-week MA
    """
    
    def __init__(self, db_manager: DatabaseManager, market_data: MarketData, notifier: Notifier):
        self.db_manager = db_manager
        self.market_data = market_data
        self.notifier = notifier
        self.ratio_calculator = RatioCalculator(market_data)
    
    def update_weekly_data(self, weeks: int = 10) -> Tuple[List[float], float]:
        """Update weekly data and calculate ratios."""
        # Get weekly prices for both symbols
        qqq_prices = self.market_data.get_weekly_prices('QQQ', weeks)
        spy_prices = self.market_data.get_weekly_prices('SPY', weeks)
        
        # Store prices in database
        self.db_manager.store_weekly_prices(qqq_prices, 'QQQ')
        self.db_manager.store_weekly_prices(spy_prices, 'SPY')
        
        # Calculate N values (QQQ/SPY ratio)
        qqq_values = list(qqq_prices.values())
        spy_values = list(spy_prices.values())
        n_values = self.market_data.calculate_ratio(qqq_values, spy_values)
        
        # Calculate V (average of N)
        v_value = self.market_data.calculate_average(n_values)
        
        # Store calculations
        self.db_manager.store_calculations(n_values, v_value)
        
        return n_values, v_value
    
    def check_current_ratio(self) -> Optional[Tuple[float, float]]:
        """Check current market ratio against stored average."""
        # First check if cached data is fresh (within 24 hours)
        if not self.db_manager.is_data_fresh(max_age_hours=24):
            print("Cached data is not fresh. Updating weekly data first...")
            self.update_weekly_data()
        elif not self.db_manager.has_data():
            print("No data in database. Updating weekly data first...")
            self.update_weekly_data()
        
        # Get latest V value
        v = self.db_manager.get_latest_v_value()
        if v is None:
            print("No V value found in database")
            return None
        
        # Get current prices
        current_prices = self.market_data.get_current_prices(['QQQ', 'SPY'])
        current_n = current_prices['QQQ'] / current_prices['SPY']
        
        return current_n, v
    
    def notify_if_signal(self, current_n: float, v: float):
        """
        Send notification if there's a trading signal.
        
        Trading rules:
        1. When N crosses above V (not just N > V):
           - If holding CASH, can buy QQQ
           - If holding SPY, must sell first
           - If holding QQQ, maintain position
           
        2. When N ≤ V:
           - If holding CASH, can buy SPY if > 40MA
           - If holding QQQ, must sell first
           - If holding SPY, maintain position if > 40MA
        """
        # Get previous state
        last_n_above_v, _, last_long_signal, _ = self.db_manager.get_last_signal_state()
        current_n_above_v = current_n > v
        
        # Rule 1: If holding QQQ and N≤V, must sell first
        if last_long_signal == "QQQ" and current_n <= v:
            title = f"QQQ与SPY比率低于均值! 当前比率({current_n:.4f})低于均值({v:.4f})"
            body = "卖出QQQ信号提醒!"
            self.notifier.send_notification(title, body)
            self.db_manager.update_signal_state(current_n_above_v, None)
            return
            
        # Rule 2: If holding SPY and N>V, must sell first
        if last_long_signal == "SPY" and current_n > v:
            title = f"SPY信号条件不满足! 当前比率({current_n:.4f})高于均值({v:.4f})"
            body = "卖出SPY信号提醒!"
            self.notifier.send_notification(title, body)
            self.db_manager.update_signal_state(current_n_above_v, None)
            return
            
        # Rule 3: Can only enter QQQ from CASH when N crosses above V
        if current_n > v and last_long_signal != "QQQ":
            if last_long_signal is None and not last_n_above_v:  # Only allow entry from CASH on upward crossover
                title = f"QQQ与SPY比率上穿均值! 当前比率({current_n:.4f})高于均值({v:.4f})"
                body = "做多QQQ信号提醒!"
                self.notifier.send_notification(title, body)
                self.db_manager.update_signal_state(current_n_above_v, "QQQ")
                
        # Rule 4: Can only enter SPY from CASH when N≤V
        elif current_n <= v and last_long_signal != "SPY":
            if last_long_signal is None:  # Only allow entry from CASH
                crossover, spy_price, ma_value = self.market_data.check_ma_crossover('SPY', ma_period=40)
                if crossover and last_n_above_v:
                    title = f"SPY突破40周均线! 当前价格({spy_price:.2f})高于均线({ma_value:.2f})"
                    body = "做多SPY信号提醒!"
                    self.notifier.send_notification(title, body)
                    self.db_manager.update_signal_state(current_n_above_v, "SPY")
            
        # 检查SPY退出信号（价格跌破40周均线）
        if last_long_signal == "SPY":
            _, spy_price, ma_value = self.market_data.check_ma_crossover('SPY', ma_period=40)
            if spy_price <= ma_value:
                title = f"SPY跌破40周均线! 当前价格({spy_price:.2f})低于均线({ma_value:.2f})"
                body = "卖出SPY信号提醒!"
                self.notifier.send_notification(title, body)
                print(f"{body}: {title}")
                self.db_manager.update_signal_state(current_n_above_v, None)