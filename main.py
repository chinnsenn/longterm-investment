"""Main entry point for the MarketFlow application."""
import logging
import time
from marketflow.config import Config
from marketflow.market_schedule import MarketSchedule
from marketflow.market_data import MarketData
from marketflow.notification import Notifier
from marketflow.database import DatabaseManager
from marketflow.ratio_calculator import QQQSPYRatioCalculator
from marketflow.strategy import Strategy

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('investment.log')
        ]
    )

def main():
    """Main function."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Initialize notifier at the start
    notifier = Notifier()
    
    try:
        # Instantiate and validate configuration
        config = Config()
        config.validate()
        config.ensure_directories()
        
        # Initialize components
        market_schedule = MarketSchedule()
        database = DatabaseManager(config.DB_PATH)
        market_data = MarketData()
        ratio_calculator = QQQSPYRatioCalculator(database, market_data, notifier)
        strategy = Strategy()
        
        # Main loop
        while True:
            try:
                if market_schedule.is_market_open() or not config.ONLY_QUERY_DURING_MARKET_HOURS:
                    # Get moving averages for QQQ and SPY
                    qqq_ma30 = market_data.get_moving_average('QQQ', period=30).iloc[-1]
                    qqq_ma50 = market_data.get_moving_average('QQQ', period=50).iloc[-1]
                    spy_ma50 = market_data.get_moving_average('SPY', period=50).iloc[-1]
                    spy_ma100 = market_data.get_moving_average('SPY', period=100).iloc[-1]
                    
                    # Get RSI values
                    qqq_rsi = market_data.get_rsi('QQQ').iloc[-1]
                    spy_rsi = market_data.get_rsi('SPY').iloc[-1]
                    
                    # Get RSI status
                    qqq_rsi_status, qqq_overbought, qqq_oversold = market_data.get_rsi_status(qqq_rsi)
                    spy_rsi_status, spy_overbought, spy_oversold = market_data.get_rsi_status(spy_rsi)
                    
                    # Check and update ratio data if needed
                    if not database.is_data_fresh(max_age_hours=24) or not database.has_data():
                        logger.info("Updating weekly ratio data...")
                        n_values, v_value = ratio_calculator.update_weekly_data()
                        logger.info(f"Updated V value: {v_value:.4f}")
                    
                    # Check current ratio and determine strategy
                    current_ratio = ratio_calculator.check_current_ratio()
                    if current_ratio:
                        n_value, v_value = current_ratio
                        logger.info(f"Current N value: {n_value:.4f}, V value: {v_value:.4f}")
                        
                        # Check strategy conditions
                        spy_ma_condition = strategy.check_spy_ma_condition()
                        strategy_position = strategy.evaluate_position(n_value, v_value, spy_ma_condition)
                        
                        # Format strategy message
                        strategy_message = (
                            "📊 投资策略分析\n"
                            "==================\n"
                            f"策略建议: {strategy_position.value}\n"
                            f"QQQ/SPY比值: {n_value:.4f}\n"
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
                        message = strategy_message + ma_message + rsi_message
                        
                        # Send notifications
                        notifier.send_bark_notification("投资策略更新", message)
                        notifier.send_telegram_notification(message)
                    
                    # Sleep for appropriate interval based on market hours
                    update_interval = config.get_update_interval()
                    logger.info(f"Sleeping for {update_interval} seconds...")
                    time.sleep(update_interval)
                else:
                    # Sleep for retry interval when market is closed
                    logger.info("Market is closed. Sleeping for retry interval...")
                    time.sleep(config.RETRY_INTERVAL)
                    
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                notifier.send_bark_notification("错误", f"运行出错: {str(e)}")
                time.sleep(300)  # Sleep for 5 minutes before retrying
                
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        notifier.send_bark_notification("严重错误", f"程序终止: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
