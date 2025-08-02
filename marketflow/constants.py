"""Constants for the MarketFlow application."""

# Time intervals (in seconds)
TRADING_UPDATE_INTERVAL = 600      # 10 minutes during trading hours
NON_TRADING_UPDATE_INTERVAL = 1800 # 30 minutes during non-trading hours
HOURLY_UPDATE_INTERVAL = 3600      # 1 hour
DAILY_UPDATE_INTERVAL = 86400      # 24 hours
RETRY_INTERVAL = 300               # 5 minutes for error retries

# Market hours (EST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# RSI thresholds
RSI_OVERBOUGHT_THRESHOLD = 70
RSI_OVERSOLD_THRESHOLD = 30

# Moving average periods
QQQ_MA30_PERIOD = 30
QQQ_MA50_PERIOD = 50
SPY_MA50_PERIOD = 50
SPY_MA100_PERIOD = 100
SPY_MA40_WEEKS = 40

# Trend analysis windows
TREND_WINDOW = 3
TREND_ANALYSIS_POINTS = 5

# Data freshness
DEFAULT_DATA_FRESHNESS_HOURS = 24
DEFAULT_CLEANUP_DAYS = 30

# Notification settings
DEFAULT_NOTIFICATION_COOLDOWN = 3600  # 1 hour
DEFAULT_ERROR_RETRY_COUNT = 3

# API timeouts
API_TIMEOUT_SECONDS = 10

# Strategy parameters
DEFAULT_WEEKS_FOR_ANALYSIS = 10
WEEKS_NEEDED_FOR_MA = 4