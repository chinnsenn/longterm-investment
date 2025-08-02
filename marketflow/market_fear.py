"""Market Fear Indicator based on VIX and volatility analysis."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from .market_data import MarketData
from .error_handling import handle_market_data_errors, retry_on_failure
from .constants import (
    VIX_SYMBOL,
    VIX_MA_PERIOD,
    VIX_LONG_MA_PERIOD,
    VIX_HISTORY_DAYS,
    VIX_EXTREME_FEAR_THRESHOLD,
    VIX_FEAR_THRESHOLD,
    VIX_GREED_THRESHOLD,
    VIX_EXTREME_GREED_THRESHOLD,
    FEAR_LEVELS
)


class MarketFearIndicator:
    """Class to calculate and analyze market fear/greed indicators based on VIX data."""
    
    def __init__(self, market_data: MarketData):
        """Initialize with a MarketData instance."""
        self.market_data = market_data
    
    def get_vix_data(self, days: int = VIX_HISTORY_DAYS) -> pd.DataFrame:
        """
        Fetch historical VIX data.
        
        Args:
            days: Number of days of historical data to fetch
            
        Returns:
            DataFrame with VIX historical data
        """
        return self.market_data.get_vix_history(days)
    
    def get_current_vix(self) -> float:
        """Get the current VIX value."""
        return self.market_data.get_current_vix()
    
    def calculate_vix_percentile(self, current_vix: float, history_days: int = VIX_HISTORY_DAYS) -> float:
        """
        Calculate the percentile rank of current VIX vs historical values.
        
        Args:
            current_vix: Current VIX value
            history_days: Number of days to look back for historical comparison
            
        Returns:
            Percentile rank (0-100)
        """
        vix_data = self.get_vix_data(history_days)
        historical_vix = vix_data['Close'].values
        
        # Calculate percentile (higher VIX = higher fear = higher percentile)
        percentile = (historical_vix < current_vix).mean() * 100
        return round(percentile, 2)
    
    def get_vix_moving_averages(self) -> Tuple[float, float]:
        """
        Get VIX moving averages for trend analysis.
        
        Returns:
            Tuple of (short_ma, long_ma) VIX moving averages
        """
        vix_data = self.get_vix_data()
        
        short_ma = vix_data['Close'].rolling(window=VIX_MA_PERIOD).mean().iloc[-1]
        long_ma = vix_data['Close'].rolling(window=VIX_LONG_MA_PERIOD).mean().iloc[-1]
        
        return float(short_ma), float(long_ma)
    
    def analyze_vix_trend(self, window: int = 5) -> str:
        """
        Analyze VIX trend direction.
        
        Args:
            window: Number of days to analyze for trend
            
        Returns:
            Trend description: 'rising', 'falling', or 'stable'
        """
        vix_data = self.get_vix_data(days=window + 5)
        recent_vix = vix_data['Close'].tail(window).values
        
        if len(recent_vix) < 2:
            return 'stable'
        
        # Calculate simple trend
        recent_change = (recent_vix[-1] - recent_vix[0]) / recent_vix[0] * 100
        
        if recent_change > 5:
            return 'rising'
        elif recent_change < -5:
            return 'falling'
        else:
            return 'stable'
    
    def calculate_fear_score(self) -> Dict[str, any]:
        """
        Calculate comprehensive fear score based on multiple factors.
        
        Returns:
            Dictionary containing fear analysis data
        """
        current_vix = self.get_current_vix()
        vix_percentile = self.calculate_vix_percentile(current_vix)
        short_ma, long_ma = self.get_vix_moving_averages()
        vix_trend = self.analyze_vix_trend()
        
        # Base fear score from VIX percentile (inverted - high VIX = high fear)
        base_score = 100 - vix_percentile
        
        # Adjust based on VIX level thresholds
        if current_vix >= VIX_EXTREME_FEAR_THRESHOLD:
            level_score = 10  # Extreme Fear
        elif current_vix >= VIX_FEAR_THRESHOLD:
            level_score = 30  # Fear
        elif current_vix <= VIX_EXTREME_GREED_THRESHOLD:
            level_score = 90  # Extreme Greed
        elif current_vix <= VIX_GREED_THRESHOLD:
            level_score = 70  # Greed
        else:
            level_score = 50  # Neutral
        
        # Adjust based on trend
        trend_adjustment = 0
        if vix_trend == 'rising':
            trend_adjustment = -10  # Increasing fear
        elif vix_trend == 'falling':
            trend_adjustment = 10   # Decreasing fear
        
        # Calculate final fear score (weighted average)
        final_score = (base_score * 0.5 + level_score * 0.3 + trend_adjustment)
        final_score = max(0, min(100, round(final_score, 0)))
        
        # Determine fear level
        fear_level = None
        for level, config in FEAR_LEVELS.items():
            if config['min'] <= final_score <= config['max']:
                fear_level = level
                break
        
        return {
            'fear_score': final_score,
            'fear_level': fear_level,
            'current_vix': current_vix,
            'vix_percentile': vix_percentile,
            'vix_short_ma': short_ma,
            'vix_long_ma': long_ma,
            'vix_trend': vix_trend,
            'timestamp': datetime.now()
        }
    
    def get_fear_status_message(self, fear_data: Dict[str, any]) -> str:
        """
        Generate a formatted fear status message.
        
        Args:
            fear_data: Fear analysis data from calculate_fear_score()
            
        Returns:
            Formatted message string
        """
        level_config = FEAR_LEVELS.get(fear_data['fear_level'], FEAR_LEVELS['NEUTRAL'])
        
        message = (
            f"市场恐惧指数: {level_config['emoji']} {level_config['label']} "
            f"({fear_data['fear_score']}/100)\n"
            f"VIX指数: {fear_data['current_vix']:.2f} "
            f"(历史百分位: {fear_data['vix_percentile']:.1f}%)\n"
            f"趋势: {self._translate_trend(fear_data['vix_trend'])}"
        )
        
        return message
    
    def _translate_trend(self, trend: str) -> str:
        """Translate VIX trend to Chinese."""
        translations = {
            'rising': '上升 🔺',
            'falling': '下降 🔻',
            'stable': '稳定 ➡️'
        }
        return translations.get(trend, '未知')