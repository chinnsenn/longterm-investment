"""Main entry point for the MarketFlow application."""
import logging
import time
from marketflow.app_setup import setup_logging, initialize_components
from marketflow.monitoring import process_market_cycle


def main():
    """Main function."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize all components
        (config, market_schedule, database, market_data, 
         ratio_calculator, strategy, notifier) = initialize_components()
        
        # Main monitoring loop
        while True:
            try:
                if market_schedule.is_market_open() or not config.ONLY_QUERY_DURING_MARKET_HOURS:
                    # Process one market cycle
                    success = process_market_cycle(
                        database, ratio_calculator, market_data, 
                        strategy, notifier, logger
                    )
                    
                    if not success:
                        logger.warning("Market cycle processing failed")
                
                # Sleep for appropriate interval based on market hours
                update_interval = config.get_update_interval()
                logger.info(f"Sleeping for {update_interval} seconds...")
                time.sleep(update_interval)
                
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