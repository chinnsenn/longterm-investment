"""Application initialization and setup utilities."""
from typing import Tuple
from marketflow.config import Config
from marketflow.market_schedule import MarketSchedule
from marketflow.market_data import MarketData
from marketflow.notification import Notifier
from marketflow.database import DatabaseManager
from marketflow.ratio_calculator import QQQSPYRatioCalculator
from marketflow.strategy import Strategy
from marketflow.error_handling import setup_logging_with_format


def setup_logging():
    """Setup logging configuration."""
    setup_logging_with_format()


def initialize_components() -> Tuple[Config, MarketSchedule, DatabaseManager, MarketData, QQQSPYRatioCalculator, Strategy, Notifier]:
    """
    Initialize all application components.
    
    Returns:
        Tuple containing all initialized components in order:
        - config: Configuration instance
        - market_schedule: Market schedule instance
        - database: Database manager instance
        - market_data: Market data instance
        - ratio_calculator: Ratio calculator instance
        - strategy: Strategy instance
        - notifier: Notification instance
    """
    # Instantiate and validate configuration
    config = Config()
    config.validate()
    config.ensure_directories()
    
    # Initialize notifier first (needed by ratio_calculator)
    notifier = Notifier()
    
    # Initialize core components
    market_schedule = MarketSchedule()
    
    # Initialize database with better error handling for permissions
    try:
        database = DatabaseManager(config.DB_PATH)
    except Exception as e:
        # Provide additional context for database initialization failures
        raise Exception(
            f"Failed to initialize database at {config.DB_PATH}. "
            f"This is often due to permissions issues. Please ensure the directory is writable. "
            f"Original error: {str(e)}"
        ) from e
        
    market_data = MarketData()
    ratio_calculator = QQQSPYRatioCalculator(database, market_data, notifier)
    strategy = Strategy()
    
    return config, market_schedule, database, market_data, ratio_calculator, strategy, notifier