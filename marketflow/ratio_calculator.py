from typing import List, Tuple, Optional
from .database import DatabaseManager
from .market_data import MarketData
from .notification import Notifier

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