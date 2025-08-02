"""Monitoring and data processing utilities."""
import logging
import time
from typing import Optional, Tuple
from marketflow.market_data import MarketData
from marketflow.strategy import Strategy
from marketflow.ratio_calculator import QQQSPYRatioCalculator
from marketflow.database import DatabaseManager
from marketflow.notification import Notifier
from marketflow.constants import (
    QQQ_MA30_PERIOD,
    QQQ_MA50_PERIOD,
    SPY_MA50_PERIOD,
    SPY_MA100_PERIOD
)


def fetch_market_indicators(market_data: MarketData) -> Tuple[float, float, float, float, float, float, str, str, bool, bool, str, str]:
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
    """
    # Get moving averages for QQQ and SPY
    qqq_ma30 = market_data.get_moving_average('QQQ', period=QQQ_MA30_PERIOD).iloc[-1]
    qqq_ma50 = market_data.get_moving_average('QQQ', period=QQQ_MA50_PERIOD).iloc[-1]
    spy_ma50 = market_data.get_moving_average('SPY', period=SPY_MA50_PERIOD).iloc[-1]
    spy_ma100 = market_data.get_moving_average('SPY', period=SPY_MA100_PERIOD).iloc[-1]
    
    # Get RSI values
    qqq_rsi = market_data.get_rsi('QQQ').iloc[-1]
    spy_rsi = market_data.get_rsi('SPY').iloc[-1]
    
    # Get RSI status
    qqq_rsi_status, qqq_overbought, qqq_oversold = market_data.get_rsi_status(qqq_rsi)
    spy_rsi_status, spy_overbought, spy_oversold = market_data.get_rsi_status(spy_rsi)
    
    return (qqq_ma30, qqq_ma50, spy_ma50, spy_ma100, qqq_rsi, spy_rsi,
            qqq_rsi_status, spy_rsi_status, qqq_overbought, qqq_oversold,
            spy_overbought, spy_oversold)


def format_notification_message(strategy_position, current_ratio: float, v_value: float, 
                               spy_ma_condition: bool, qqq_ma30: float, qqq_ma50: float,
                               spy_ma50: float, spy_ma100: float, qqq_rsi: float,
                               spy_rsi: float, qqq_rsi_status: str, spy_rsi_status: str,
                               qqq_overbought: bool, qqq_oversold: bool,
                               spy_overbought: bool, spy_oversold: bool) -> str:
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
    
    # Combine all messages
    return strategy_message + ma_message + rsi_message


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
        strategy_position = strategy.evaluate_position(n_value, v_value, spy_ma_condition)
        
        # Fetch all market indicators
        (qqq_ma30, qqq_ma50, spy_ma50, spy_ma100, qqq_rsi, spy_rsi,
         qqq_rsi_status, spy_rsi_status, qqq_overbought, qqq_oversold,
         spy_overbought, spy_oversold) = fetch_market_indicators(market_data)
        
        # Format and send notification
        message = format_notification_message(
            strategy_position, n_value, v_value, spy_ma_condition,
            qqq_ma30, qqq_ma50, spy_ma50, spy_ma100,
            qqq_rsi, spy_rsi, qqq_rsi_status, spy_rsi_status,
            qqq_overbought, qqq_oversold, spy_overbought, spy_oversold
        )
        
        # Send notifications
        notifier.send_bark_notification("投资策略更新", message)
        notifier.send_telegram_notification(message)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in market processing cycle: {str(e)}")
        return False