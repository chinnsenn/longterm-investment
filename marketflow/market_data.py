import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

class MarketData:
    @staticmethod
    def get_weekly_prices(symbol: str, weeks: int = 10) -> Dict[datetime, float]:
        """Fetch weekly prices from Yahoo Finance."""
        try:
            today = datetime.now()
            start_date = today - timedelta(weeks=weeks+2)
            
            ticker = yf.Ticker(symbol)
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
    def get_current_prices(symbols: List[str]) -> Dict[str, float]:
        """Get current market prices for given symbols."""
        if not symbols:
            raise ValueError("No symbols provided")
            
        prices = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="1d")
                if df.empty:
                    raise ValueError(f"No data available for symbol {symbol}")
                prices[symbol] = df['Close'].iloc[-1]
            except Exception as e:
                raise Exception(f"Error fetching price for {symbol}: {str(e)}")
        return prices
    
    @staticmethod
    def get_latest_price(symbol: str) -> float:
        """Get the latest price for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
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
    def check_ma_crossover(symbol: str, ma_period: int = 40) -> Tuple[bool, float, float]:
        """
        检查价格是否突破移动平均线，使用趋势确认。
        """
        try:
            # 获取足够的数据用于MA计算和趋势判断
            weeks_needed = ma_period + 4
            today = datetime.now()
            start_date = today - timedelta(weeks=weeks_needed)
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # 计算周数据
            df = df.reset_index()
            df['Date'] = pd.to_datetime(df['Date'])
            weekly_data = df.set_index('Date').resample('W-FRI').last()
            weekly_data = weekly_data.dropna()
            
            # 计算MA
            weekly_data['MA'] = weekly_data['Close'].rolling(window=ma_period).mean()
            
            # 获取最近的价格数据用于趋势判断
            prices = weekly_data['Close'].values
            ma_values = weekly_data['MA'].dropna().values
            
            if len(prices) < 4 or len(ma_values) < 4:
                raise ValueError(f"Insufficient data for trend analysis")
            
            # 检查趋势和突破
            upward_cross, _, slope = MarketData.check_crossover_trend(
                prices[-5:].tolist(),  # 使用最近5周数据
                ma_values[-1],         # 当前MA值
                window=3              # 使用3周趋势
            )
            
            return upward_cross, prices[-1], ma_values[-1]
            
        except Exception as e:
            raise Exception(f"Error checking MA crossover for {symbol}: {str(e)}")
            
    @staticmethod
    def check_ratio_crossover(symbol1: str, symbol2: str, window: int = 10) -> Tuple[bool, float, float]:
        """
        检查两个股票的比率是否突破其均值，使用趋势确认。
        """
        try:
            today = datetime.now()
            start_date = today - timedelta(weeks=window+4)  # 多获取一些数据用于趋势判断
            
            # 获取两个股票的历史数据
            ticker1 = yf.Ticker(symbol1)
            ticker2 = yf.Ticker(symbol2)
            df1 = ticker1.history(start=start_date, end=today)
            df2 = ticker2.history(start=start_date, end=today)
            
            if df1.empty or df2.empty:
                raise ValueError(f"No data available for one or both symbols: {symbol1}, {symbol2}")
            
            # 计算比率
            df = pd.DataFrame()
            df['Date'] = df1.index
            df['Ratio'] = df1['Close'] / df2['Close']
            
            # 计算比率的移动平均
            df['MA'] = df['Ratio'].rolling(window=window).mean()
            
            # 获取最近的比率数据用于趋势判断
            ratios = df['Ratio'].values
            ma_values = df['MA'].dropna().values
            
            if len(ratios) < 4 or len(ma_values) < 4:
                raise ValueError(f"Insufficient data for ratio trend analysis")
            
            # 检查趋势和突破
            upward_cross, _, slope = MarketData.check_crossover_trend(
                ratios[-5:].tolist(),  # 使用最近5个数据点
                ma_values[-1],         # 当前MA值
                window=3              # 使用3点趋势
            )
            
            return upward_cross, ratios[-1], ma_values[-1]
            
        except Exception as e:
            raise Exception(f"Error checking ratio crossover: {str(e)}")
    
    @staticmethod
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
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=today)
            
            if df.empty:
                raise ValueError(f"No data available for symbol {symbol}")
            
            # Calculate moving average
            ma = df['Close'].rolling(window=period).mean()
            return ma
            
        except Exception as e:
            raise Exception(f"Error calculating moving average for {symbol}: {str(e)}")
            
    @staticmethod
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
            
            ticker = yf.Ticker(symbol)
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