"""Monitoring and data processing utilities."""
import logging
import time
import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from marketflow.market_data import MarketData
from marketflow.strategy import Strategy
from marketflow.ratio_calculator import QQQSPYRatioCalculator
from marketflow.database import DatabaseManager
from marketflow.notification import Notifier
from marketflow.market_fear import MarketFearIndicator
from marketflow.constants import (
    QQQ_MA30_PERIOD,
    QQQ_MA50_PERIOD,
    SPY_MA50_PERIOD,
    SPY_MA100_PERIOD
)


def fetch_market_indicators(market_data: MarketData, fear_indicator: MarketFearIndicator) -> Tuple[float, float, float, float, float, float, str, str, bool, bool, str, str, Dict[str, Any], str, str, float]:
    """
    Fetch all market indicators and technical analysis data.
    
    Returns:
        Tuple containing:
        - qqq_ma30: QQQ 30-day moving average
        - qqq_ma50: QQQ 50-day moving average
        - spy_ma50: SPY 50-day moving average
        - spy_ma100: SPY 100-day moving average
        - qqq_rsi: QQQ RSI value
        - spy_rsi: SPY RSI value
        - qqq_rsi_status: QQQ RSI status string
        - spy_rsi_status: SPY RSI status string
        - qqq_overbought: QQQ overbought flag
        - qqq_oversold: QQQ oversold flag
        - spy_overbought: SPY overbought flag
        - spy_oversold: SPY oversold flag
        - fear_data: Fear indicator data dictionary
        - qqq_ma_trend: QQQ moving average trend
        - spy_ma_trend: SPY moving average trend
        - dynamic_threshold: Dynamic threshold value
    """
    # Get moving averages for QQQ and SPY
    qqq_ma_series = market_data.get_moving_average('QQQ', period=QQQ_MA30_PERIOD)
    qqq_ma30 = qqq_ma_series.iloc[-1]
    qqq_ma50_series = market_data.get_moving_average('QQQ', period=QQQ_MA50_PERIOD)
    qqq_ma50 = qqq_ma50_series.iloc[-1]
    spy_ma50_series = market_data.get_moving_average('SPY', period=SPY_MA50_PERIOD)
    spy_ma50 = spy_ma50_series.iloc[-1]
    spy_ma100_series = market_data.get_moving_average('SPY', period=SPY_MA100_PERIOD)
    spy_ma100 = spy_ma100_series.iloc[-1]
    
    # Determine moving average trends
    qqq_ma_trend = _determine_trend(qqq_ma_series)
    spy_ma_trend = _determine_trend(spy_ma50_series)
    
    # Get RSI values
    qqq_rsi_series = market_data.get_rsi('QQQ')
    qqq_rsi = qqq_rsi_series.iloc[-1]
    spy_rsi_series = market_data.get_rsi('SPY')
    spy_rsi = spy_rsi_series.iloc[-1]
    
    # Get RSI status
    qqq_rsi_status, qqq_overbought, qqq_oversold = market_data.get_rsi_status(qqq_rsi)
    spy_rsi_status, spy_overbought, spy_oversold = market_data.get_rsi_status(spy_rsi)
    
    # Calculate fear indicator data
    fear_data = fear_indicator.calculate_fear_score()
    
    # Calculate dynamic threshold (placeholder, would need more data in practice)
    dynamic_threshold = 1.0
    
    return (qqq_ma30, qqq_ma50, spy_ma50, spy_ma100, qqq_rsi, spy_rsi,
            qqq_rsi_status, spy_rsi_status, qqq_overbought, qqq_oversold,
            spy_overbought, spy_oversold, fear_data, qqq_ma_trend, spy_ma_trend, dynamic_threshold)


def _determine_trend(ma_series: pd.Series) -> str:
    """
    Determine the trend based on moving average series.
    
    Args:
        ma_series: Moving average series
        
    Returns:
        Trend direction ('rising', 'falling', or 'stable')
    """
    if len(ma_series) < 3:
        return 'stable'
        
    # Calculate recent changes
    recent_values = ma_series.tail(3).values
    changes = np.diff(recent_values)
    
    # Determine trend based on recent changes
    if all(change > 0 for change in changes):
        return 'rising'
    elif all(change < 0 for change in changes):
        return 'falling'
    else:
        return 'stable'


def format_notification_message(strategy_position, current_ratio: float, v_value: float, 
                               spy_ma_condition: bool, qqq_ma30: float, qqq_ma50: float,
                               spy_ma50: float, spy_ma100: float, qqq_rsi: float,
                               spy_rsi: float, qqq_rsi_status: str, spy_rsi_status: str,
                               qqq_overbought: bool, qqq_oversold: bool,
                               spy_overbought: bool, spy_oversold: bool,
                               fear_data: Dict[str, Any], fear_indicator: MarketFearIndicator) -> str:
    """
    Format the complete notification message with all market data.
    """
    # Format strategy message
    strategy_message = (
        "📊 投资策略分析\n"
        "==================\n"
        f"策略建议: {strategy_position.value}\n"
        f"QQQ/SPY比值: {current_ratio:.4f}\n"
        f"阈值: {v_value:.4f}\n"
        f"SPY均线条件: {'✅ 满足' if spy_ma_condition else '❌ 不满足'}"
    )
    
    # Format moving average message
    ma_message = (
        "\n\n📈 移动平均线\n"
        "==================\n"
        "QQQ:\n"
        f"  MA30: {qqq_ma30:.2f}\n"
        f"  MA50: {qqq_ma50:.2f}\n"
        "SPY:\n"
        f"  MA50: {spy_ma50:.2f}\n"
        f"  MA100: {spy_ma100:.2f}"
    )
    
    # Format RSI message
    rsi_message = (
        "\n\n📉 RSI指标\n"
        "==================\n"
        f"QQQ (14日): {qqq_rsi:.1f} {qqq_rsi_status}\n"
        f"SPY (14日): {spy_rsi:.1f} {spy_rsi_status}"
    )
    
    # Format fear indicator message
    fear_message = (
        "\n\n😱 市场恐惧指数\n"
        "==================\n"
        f"{fear_indicator.get_fear_status_message(fear_data)}"
    )
    
    # Combine all messages
    return strategy_message + ma_message + rsi_message + fear_message


def process_market_cycle(database: DatabaseManager, ratio_calculator: QQQSPYRatioCalculator,
                        market_data: MarketData, strategy: Strategy, notifier: Notifier,
                        logger: logging.Logger) -> bool:
    """
    Process one complete market monitoring cycle.
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Check and update ratio data if needed
        if not database.is_data_fresh(max_age_hours=24) or not database.has_data():
            logger.info("Updating weekly ratio data...")
            n_values, v_value = ratio_calculator.update_weekly_data()
            logger.info(f"Updated V value: {v_value:.4f}")
        
        # Check current ratio and determine strategy
        current_ratio = ratio_calculator.check_current_ratio()
        if not current_ratio:
            logger.warning("Could not get current ratio")
            return False
            
        n_value, v_value = current_ratio
        logger.info(f"Current N value: {n_value:.4f}, V value: {v_value:.4f}")
        
        # Check strategy conditions
        spy_ma_condition = strategy.check_spy_ma_condition()
        
        # Initialize fear indicator
        fear_indicator = MarketFearIndicator(market_data)
        
        # Fetch all market indicators
        (qqq_ma30, qqq_ma50, spy_ma50, spy_ma100, qqq_rsi, spy_rsi,
         qqq_rsi_status, spy_rsi_status, qqq_overbought, qqq_oversold,
         spy_overbought, spy_oversold, fear_data, qqq_ma_trend, spy_ma_trend, 
         dynamic_threshold) = fetch_market_indicators(market_data, fear_indicator)
        
        # Use enhanced strategy evaluation with multi-factor confirmation
        strategy_position = strategy.evaluate_position_enhanced(
            n_value, v_value, spy_ma_condition, qqq_rsi, spy_rsi, 
            qqq_ma_trend, spy_ma_trend, fear_data['fear_score']
        )
        
        # Format and send notification
        message = format_notification_message(
            strategy_position, n_value, v_value, spy_ma_condition,
            qqq_ma30, qqq_ma50, spy_ma50, spy_ma100,
            qqq_rsi, spy_rsi, qqq_rsi_status, spy_rsi_status,
            qqq_overbought, qqq_oversold, spy_overbought, spy_oversold,
            fear_data, fear_indicator
        )
        
        # Store VIX data in database
        database.store_vix_data(
            fear_data['current_vix'],
            fear_data['vix_percentile'],
            fear_data['fear_score'],
            fear_data['fear_level']
        )
        
        # Update entry prices for stop loss tracking
        if strategy_position == strategy.current_position:
            # No position change, update trailing stops
            current_prices = market_data.get_current_prices(['QQQ', 'SPY'])
            for symbol in ['QQQ', 'SPY']:
                if symbol in current_prices:
                    strategy.update_entry_price(symbol, current_prices[symbol])
        
        # Check stop loss conditions
        current_positions = {'QQQ': qqq_ma30, 'SPY': spy_ma50}  # Simplified
        current_prices = market_data.get_current_prices(['QQQ', 'SPY'])
        stop_loss_symbols = strategy.check_stop_loss(current_positions, current_prices)
        
        if stop_loss_symbols:
            logger.info(f"Stop loss triggered for symbols: {stop_loss_symbols}")
            # In a real implementation, this would trigger position exits
        
        # Send notifications
        notifier.send_bark_notification("投资策略更新", message)
        notifier.send_telegram_notification(message)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in market processing cycle: {str(e)}")
        return False