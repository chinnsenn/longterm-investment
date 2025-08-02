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

# VIX and Fear Indicator constants
VIX_SYMBOL = '^VIX'
VIX_MA_PERIOD = 20
VIX_LONG_MA_PERIOD = 50
VIX_HISTORY_DAYS = 252  # 1 year for percentile calculations
VIX_EXTREME_FEAR_THRESHOLD = 35
VIX_FEAR_THRESHOLD = 25
VIX_GREED_THRESHOLD = 15
VIX_EXTREME_GREED_THRESHOLD = 10

# Fear indicator levels
FEAR_LEVELS = {
    'EXTREME_FEAR': {'min': 0, 'max': 20, 'emoji': '😱', 'label': '极度恐惧'},
    'FEAR': {'min': 21, 'max': 40, 'emoji': '😨', 'label': '恐惧'},
    'NEUTRAL': {'min': 41, 'max': 60, 'emoji': '😐', 'label': '中性'},
    'GREED': {'min': 61, 'max': 80, 'emoji': '😊', 'label': '贪婪'},
    'EXTREME_GREED': {'min': 81, 'max': 100, 'emoji': '🤑', 'label': '极度贪婪'}
}