# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarketFlow is a sophisticated quantitative trading system that implements an adaptive QQQ/SPY rotation strategy based on relative strength analysis and moving averages. The system monitors real-time market data, calculates technical indicators, and generates trading signals with automated notifications.

## Development Commands

### Running the Application
```bash
# Run the main application
python main.py

# Run with development logging
python main.py --debug
```

### Docker Development
```bash
# Build Docker image
docker build -t marketflow .

# Run with Docker
docker run -d --name marketflow --restart unless-stopped -v $(pwd)/.env:/app/.env -v $(pwd)/data:/app/data marketflow

# Using Docker Compose (recommended)
docker compose up -d        # Start
docker compose logs -f      # View logs
docker compose down         # Stop
```

### Dependency Management
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Update specific dependencies
pip install --upgrade yfinance>=0.2.54
```

### Testing
The project uses pytest for testing (though test files are currently not visible in the repository). Coverage reports indicate approximately 50% test coverage across core modules.

```bash
# Run tests (when tests directory is present)
pytest

# Run with coverage
pytest --cov=marketflow --cov-report=html
```

## Architecture Overview

### Core Components

**Entry Point**: `main.py`
- Orchestrates the application flow
- Initializes all modules and runs the main monitoring loop
- Implements intelligent update intervals based on market hours

**Configuration Module**: `marketflow/config.py`
- Environment-based configuration management
- Market hour calculations (EST to Beijing time conversion)
- Dynamic update intervals based on trading status

**Database Layer**: `marketflow/database.py`
- SQLite backend with three core tables:
  - `weekly_prices`: Historical price data
  - `calculations`: Computed N values (QQQ/SPY ratios) and V values (averages)
  - `signal_state`: Trading signal history and position tracking
- Data freshness validation and cleanup

**Market Data Engine**: `marketflow/market_data.py`
- Yahoo Finance API integration via yfinance
- Technical calculations:
  - Moving averages (MA30, MA50, MA100)
  - RSI indicators with overbought/oversold detection
  - QQQ/SPY ratio calculations
- Crossover detection with trend confirmation

**Strategy Engine**: `marketflow/strategy.py`
- Implements position states: CASH, QQQ, SPY, SH, PSQ, AGG, LQD, TLT, GLD
- Entry/exit rules:
  - QQQ: Buy when ratio > threshold
  - SPY: Buy when ratio ≤ threshold AND SPY > 40-week MA
  - Must pass through CASH when switching positions

**Ratio Calculator**: `marketflow/ratio_calculator.py`
- Core business logic for QQQ/SPY ratio calculations
- Weekly data updates and V value computations
- Signal generation triggers

**Market Schedule**: `marketflow/market_schedule.py`
- US market hours management using exchange-calendars
- Time zone handling and trading day validation

**Notification System**: `marketflow/notification.py`
- Multi-channel support: Bark API and Telegram Bot
- HTML-formatted messages with cooldown periods
- Retry mechanisms and error handling

### Data Flow

1. **Market Data Fetch**: Yahoo Finance API retrieves real-time QQQ/SPY data
2. **Technical Analysis**: Calculate moving averages, RSI, and ratios
3. **Signal Generation**: Strategy engine evaluates conditions
4. **State Management**: Database tracks signals and position history
5. **Notification**: Alerts sent via configured channels on signal changes

### Configuration Management

The `.env` file controls:
- API keys (BARK_API_KEY, TELEGRAM_BOT_TOKEN)
- Database path (DB_PATH)
- Update intervals (UPDATE_INTERVAL_SECONDS)
- Notification settings (COOLDOWN_MINUTES)
- Market hour restrictions (MARKET_HOURS_ONLY)

## Key Implementation Details

### Market Hours Logic
- US market hours: 9:30 AM - 4:00 PM EST
- Automatic conversion to Beijing time
- Extended update intervals during non-market hours
- Trading day validation using exchange calendars

### Trading Strategy Rules
- Tracks QQQ/SPY ratio (N) vs historical average (V)
- Position switching must go through CASH state
- Includes RSI indicators for overbought/oversold confirmation
- Supports multiple ETFs and inverse ETFs

### Error Handling
- Comprehensive exception handling throughout
- Retry mechanisms for API failures
- Graceful degradation when services are unavailable
- Detailed logging for troubleshooting

## Development Notes

### Dependencies
- Core: Python 3.8+, pandas, numpy, yfinance
- Time handling: pytz, python-dateutil, exchange-calendars
- HTTP: requests for notification APIs
- Configuration: python-dotenv

### Package Structure
- Main application code in `marketflow/` directory
- Configuration via `.env` (template in `.env.example`)
- Docker deployment ready with multi-stage build
- Data persistence in SQLite database (default: `data/marketflow.db`)

### Working with Market Data
- The system caches data to minimize API calls
- Weekly price updates occur on Fridays
- Real-time monitoring during market hours
- Historical data stored for backtesting and analysis

### Extending the System
- Add new indicators in `market_data.py`
- Implement new strategies in `strategy.py`
- Add notification channels in `notification.py`
- Extend database schema in `database.py`