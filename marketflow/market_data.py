import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
from .error_handling import handle_market_data_errors, retry_on_failure
from .constants import API_TIMEOUT_SECONDS, DEFAULT_WEEKS_FOR_ANALYSIS, WEEKS_NEEDED_FOR_MA

class MarketData:
    @staticmethod
    def _get_ticker(symbol: str):
        """Get yfinance Ticker object for a symbol."""
        return yf.Ticker(symbol)
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_weekly_prices(symbol: str, weeks: int = DEFAULT_WEEKS_FOR_ANALYSIS) -> Dict[datetime, float]:
        """Fetch weekly prices from Yahoo Finance."""
        try:
            today = datetime.now()
            start_date = today - timedelta(weeks=weeks+2)
            
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            df = df.reset_index()
            df['Date'] = pd.to_datetime(df['Date'])
            
            weekly_data = df.set_index('Date').resample('W-FRI').last()
            weekly_data = weekly_data.dropna()
            
            result = weekly_data['Close'].tail(weeks).to_dict()
            if not result:
                raise ValueError(f"Insufficient data for symbol {symbol}")
                
            return result
        except Exception as e:
            raise ValueError(f"Error fetching data for {symbol}: {str(e)}")
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_current_prices(symbols: List[str]) -> Dict[str, float]:
        """Get current market prices for given symbols."""
        if not symbols:
            raise ValueError("No symbols provided")
            
        prices = {}
        for symbol in symbols:
            try:
                ticker = MarketData._get_ticker(symbol)
                df = ticker.history(period="1d")
                if df.empty:
                    raise ValueError(f"No data available for symbol {symbol}")
                prices[symbol] = df['Close'].iloc[-1]
            except Exception as e:
                raise Exception(f"Error fetching price for {symbol}: {str(e)}")
        return prices
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_latest_price(symbol: str) -> float:
        """Get the latest price for a symbol."""
        try:
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(period="1d")
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            return float(df['Close'].iloc[-1])
        except Exception as e:
            raise ValueError(f"Error fetching latest price for {symbol}: {str(e)}")
    
    @staticmethod
    def calculate_ratio(prices1: List[float], prices2: List[float]) -> List[float]:
        """Calculate ratio between two price series."""
        if len(prices1) != len(prices2):
            raise ValueError("Price series must have the same length")
        if not prices1 or not prices2:
            raise ValueError("Price series cannot be empty")
        if any(p2 == 0 for p2 in prices2):
            raise ValueError("Denominator prices cannot contain zero")
            
        return [p1 / p2 for p1, p2 in zip(prices1, prices2)]
    
    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of a list of values."""
        if not values:
            raise ValueError("Cannot calculate average of empty list")
        return sum(values) / len(values)
    
    @staticmethod
    def check_crossover_trend(values: List[float], threshold: float, window: int = 3) -> Tuple[bool, bool, float]:
        """
        检查是否发生了有效的上穿/下穿，通过分析多个数据点来确认趋势。
        
        Args:
            values: 最近的价格序列，按时间正序排列
            threshold: 阈值（如均线值）
            window: 用于判断趋势的窗口大小
            
        Returns:
            Tuple[bool, bool, float]:
                - 是否发生上穿
                - 是否发生下穿
                - 当前趋势斜率
        """
        if len(values) < window + 1:
            return False, False, 0.0
            
        # 计算最近window个点的趋势斜率
        recent_values = values[-window:]
        x = np.arange(len(recent_values))
        slope = np.polyfit(x, recent_values, 1)[0]
        
        # 获取当前值和前一个值相对于阈值的位置
        curr_value = values[-1]
        prev_value = values[-2]
        
        # 判断是否所有最近的点都在形成趋势
        is_trending_up = all(values[i] < values[i+1] for i in range(-window, -1))
        is_trending_down = all(values[i] > values[i+1] for i in range(-window, -1))
        
        # 上穿条件：
        # 1. 当前值在阈值上方
        # 2. 前一个值在阈值下方
        # 3. 近期趋势向上（斜率为正）
        # 4. 最近的点都在形成上升趋势
        upward_crossover = (
            curr_value > threshold and
            prev_value <= threshold and
            slope > 0 and
            is_trending_up
        )
        
        # 下穿条件类似
        downward_crossover = (
            curr_value < threshold and
            prev_value >= threshold and
            slope < 0 and
            is_trending_down
        )
        
        return upward_crossover, downward_crossover, slope
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_moving_average(symbol: str, period: int = 20, days: int = 100) -> pd.Series:
        """
        Calculate the moving average for a given stock symbol and period.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            period (int): Moving average period (e.g., 20 for 20-day MA)
            days (int): Number of days of historical data to fetch
            
        Returns:
            pd.Series: Moving average series
        """
        try:
            # Fetch historical data
            today = datetime.now()
            start_date = today - timedelta(days=days+period)
            
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # Calculate moving average
            ma = df['Close'].rolling(window=period).mean()
            return ma
            
        except Exception as e:
            raise Exception(f"Error calculating moving average for {symbol}: {str(e)}")
            
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_rsi(symbol: str, period: int = 14, days: int = 100) -> pd.Series:
        """
        Calculate the Relative Strength Index (RSI) for a given stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            period (int): RSI period (default: 14 days)
            days (int): Number of days of historical data to fetch
            
        Returns:
            pd.Series: RSI values series
        """
        try:
            # Fetch historical data
            today = datetime.now()
            start_date = today - timedelta(days=days+period)
            
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # Calculate daily price changes
            delta = df['Close'].diff()
            
            # Separate gains (up) and losses (down)
            gain = (delta.where(delta > 0, 0))
            loss = (-delta.where(delta < 0, 0))
            
            # Calculate average gains and losses over the specified period
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # Calculate RS (Relative Strength)
            rs = avg_gain / avg_loss
            
            # Calculate RSI
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            raise Exception(f"Error calculating RSI for {symbol}: {str(e)}")
    
    @staticmethod
    def get_rsi_status(rsi: float, overbought_threshold: float = 70, oversold_threshold: float = 30) -> tuple[str, bool, bool]:
        """
        Get the RSI status indicating if it's in overbought or oversold territory.
        
        Args:
            rsi (float): RSI value
            overbought_threshold (float): Threshold for overbought condition (default: 70)
            oversold_threshold (float): Threshold for oversold condition (default: 30)
            
        Returns:
            tuple[str, bool, bool]: (Status message, is_overbought, is_oversold)
        """
        is_overbought = rsi >= overbought_threshold
        is_oversold = rsi <= oversold_threshold
        
        if is_overbought:
            return " 超买", True, False
        elif is_oversold:
            return " 超卖", False, True
        return "正常", False, False
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_vix_history(days: int = 252) -> pd.DataFrame:
        """
        Get historical VIX data.
        
        Args:
            days: Number of days of historical data
            
        Returns:
            DataFrame with VIX historical data
        """
        today = datetime.now()
        start_date = today - timedelta(days=days)
        
        ticker = MarketData._get_ticker('^VIX')
        df = ticker.history(start=start_date, end=today)
        
        if df.empty:
            raise ValueError("No VIX data available")
        
        return df
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_current_vix() -> float:
        """Get current VIX value."""
        ticker = MarketData._get_ticker('^VIX')
        df = ticker.history(period="1d")
        
        if df.empty:
            raise ValueError("No VIX data available")
        
        return float(df['Close'].iloc[-1])
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_macd(symbol: str, fast_period: int = 12, slow_period: int = 26, 
                 signal_period: int = 9, days: int = 100) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence) for a given stock symbol.
        
        Args:
            symbol (str): Stock symbol
            fast_period (int): Fast EMA period (default: 12)
            slow_period (int): Slow EMA period (default: 26)
            signal_period (int): Signal line period (default: 9)
            days (int): Number of days of historical data to fetch
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (MACD line, Signal line, Histogram)
        """
        try:
            # Fetch historical data
            today = datetime.now()
            start_date = today - timedelta(days=days+slow_period)
            
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # Calculate EMAs
            ema_fast = df['Close'].ewm(span=fast_period).mean()
            ema_slow = df['Close'].ewm(span=slow_period).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            raise Exception(f"Error calculating MACD for {symbol}: {str(e)}")
    
    @staticmethod
    def get_macd_status(macd_line: float, signal_line: float) -> Tuple[str, bool]:
        """
        Get MACD status and bullish/bearish signal.
        
        Returns:
            Tuple[str, bool]: (Status message, is_bullish)
        """
        is_bullish = macd_line > signal_line
        status = "金叉 ✅" if is_bullish else "死叉 ❌"
        return status, is_bullish
    
    @staticmethod
    @retry_on_failure(max_retries=3)
    @handle_market_data_errors
    def get_bollinger_bands(symbol: str, period: int = 20, std_dev: int = 2, 
                           days: int = 100) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands for a given stock symbol.
        
        Args:
            symbol (str): Stock symbol
            period (int): Period for moving average (default: 20)
            std_dev (int): Standard deviation multiplier (default: 2)
            days (int): Number of days of historical data to fetch
            
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (Upper band, Middle band, Lower band)
        """
        try:
            # Fetch historical data
            today = datetime.now()
            start_date = today - timedelta(days=days+period)
            
            ticker = MarketData._get_ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # Calculate middle band (SMA)
            middle_band = df['Close'].rolling(window=period).mean()
            
            # Calculate standard deviation
            std = df['Close'].rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            return upper_band, middle_band, lower_band
            
        except Exception as e:
            raise Exception(f"Error calculating Bollinger Bands for {symbol}: {str(e)}")
    
    @staticmethod
    def get_bollinger_band_position(current_price: float, upper_band: float, 
                                   middle_band: float, lower_band: float) -> str:
        """
        Determine position relative to Bollinger Bands.
        """
        if current_price > upper_band:
            return "超买区 🔥"
        elif current_price < lower_band:
            return "超卖区 🧊"
        elif current_price > middle_band:
            return "中轨上方 📈"
        else:
            return "中轨下方 📉"