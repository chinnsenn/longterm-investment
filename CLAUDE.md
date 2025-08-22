# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MarketFlow is a sophisticated quantitative trading system that implements an adaptive QQQ/SPY rotation strategy based on relative strength analysis, moving averages, and market sentiment indicators. The system monitors real-time market data, calculates technical indicators including VIX-based fear/greed metrics, and generates trading signals with automated notifications.

## Development Commands

### Running the Application
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run the main application
python main.py

# Run with development logging
python main.py --debug
```

### Docker Development
The project uses standard pip for dependency management in Docker with multi-stage builds for optimized images.

```bash
# Build Docker image (production)
docker build -t marketflow .

# Build development image with dev dependencies
docker build --target development -t marketflow:dev

# Run with Docker
docker run -d --name marketflow --restart unless-stopped -v $(pwd)/.env:/app/.env -v $(pwd)/data:/app/data marketflow

# Using Docker Compose (recommended)
docker compose up -d                    # Start production
docker compose --profile dev up -d       # Start development
docker compose logs -f                  # View logs
docker compose down                     # Stop
```

### Dependency Management

#### Using UV venv (Recommended)
UV provides up to 80x faster dependency resolution and installation.

```bash
# Install UV (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with UV
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies with UV
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"

# Run the application
python main.py

# Run with development logging
python main.py --debug

# Update specific dependencies
uv pip install --upgrade yfinance>=0.2.54

# Add new dependencies
uv add <package-name>

# Remove dependencies
uv remove <package-name>
```

#### Using pip (Traditional)
```bash
# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Update specific dependencies
pip install --upgrade yfinance>=0.2.54
```

### Testing
The project uses pytest for testing with coverage reports.

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=marketflow --cov-report=html
```

### Code Quality
The project uses Black for code formatting, Ruff for linting, and MyPy for type checking.

```bash
# Activate virtual environment first
source .venv/bin/activate

# Format code with Black
black .

# Lint with Ruff
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Type checking with MyPy
mypy .
```

## Architecture Overview

### Core Components

**Entry Point**: `main.py`
- Orchestrates the application flow through modular components
- Initializes all modules via `app_setup.initialize_components()`
- Runs the main monitoring loop with intelligent update intervals based on market hours

**Application Setup**: `marketflow/app_setup.py`
- Centralized component initialization and dependency injection
- Logging configuration with standardized formatting
- Returns ordered tuple of all core components for easy instantiation

**Configuration Module**: `marketflow/config.py`
- Environment-based configuration management with validation
- Market hour calculations (EST to Beijing time conversion)
- Dynamic update intervals based on trading status and market conditions

**Constants**: `marketflow/constants.py`
- Centralized constants for all modules including time intervals, thresholds, and periods
- VIX and fear indicator constants with predefined fear levels
- Trading parameters and API timeouts

**Error Handling**: `marketflow/error_handling.py`
- Decorator-based error handling for consistent exception management
- Retry mechanisms with configurable attempts
- Specialized handlers for different error types (database, market data)

**Database Layer**: `marketflow/database.py`
- SQLite backend with four core tables:
  - `weekly_prices`: Historical price data for QQQ/SPY
  - `calculations`: Computed N values (QQQ/SPY ratios) and V values (averages)
  - `signal_state`: Trading signal history and position tracking
  - `vix_history`: VIX data and fear indicator historical records
- Data freshness validation, cleanup, and comprehensive CRUD operations
- Docker-compatible logging with volume mounts for log persistence

**Market Data Engine**: `marketflow/market_data.py`
- Yahoo Finance API integration via yfinance with error handling
- Technical calculations:
  - Moving averages (configurable periods)
  - RSI indicators with overbought/oversold detection
  - QQQ/SPY ratio calculations
  - VIX data fetching and historical analysis
- Crossover detection with trend confirmation using multiple data points

**Market Fear Indicator**: `marketflow/market_fear.py`
- VIX-based market sentiment analysis with historical context
- Fear score calculation (0-100) using multiple factors:
  - Current VIX vs historical percentile
  - VIX moving averages and trend analysis
  - Threshold-based fear level classification
- Five-level fear gauge with emoji indicators for notifications

**Strategy Engine**: `marketflow/strategy.py`
- Implements position states: CASH, QQQ, SPY, SH, PSQ, AGG, LQD, TLT, GLD
- Entry/exit rules with confirmation mechanisms:
  - QQQ: Buy when ratio > threshold
  - SPY: Buy when ratio ≤ threshold AND SPY > 40-week MA
  - Must pass through CASH when switching positions (no direct ETF-to-ETF switches)

**Ratio Calculator**: `marketflow/ratio_calculator.py`
- Core business logic for QQQ/SPY ratio calculations
- Weekly data updates and V value computations using historical averages
- Signal generation triggers with notification integration

**Market Schedule**: `marketflow/market_schedule.py`
- US market hours management using exchange-calendars
- Time zone handling and trading day validation with holiday support

**Monitoring**: `marketflow/monitoring.py`
- Centralized market cycle processing with comprehensive indicator fetching
- Formats notification messages with all technical and sentiment data
- Orchestrates the complete analysis workflow in each cycle

**Notification System**: `marketflow/notification.py`
- Multi-channel support: Bark API and Telegram Bot
- HTML-formatted messages with structured sections and cooldown periods
- Retry mechanisms and error handling for delivery assurance

### Data Flow

1. **Initialization**: `app_setup.py` creates and wires all components
2. **Market Cycle**: `monitoring.py.process_market_cycle()` orchestrates one complete analysis
3. **Data Fetch**: Yahoo Finance API retrieves real-time QQQ/SPY/VIX data
4. **Technical Analysis**: Calculate moving averages, RSI, ratios, and fear indicators
5. **Signal Generation**: Strategy engine evaluates all conditions including sentiment
6. **State Management**: Database tracks signals, positions, and VIX history
7. **Notification**: Structured alerts sent via configured channels with comprehensive data

### Configuration Management

The `.env` file controls:
- API keys (BARK_API_KEY, TELEGRAM_BOT_TOKEN)
- Database path (DB_PATH)
- Update intervals and retry behavior
- Notification settings (COOLDOWN_MINUTES, ERROR_RETRY_COUNT)
- Market hour restrictions (ONLY_QUERY_DURING_MARKET_HOURS)

## Key Implementation Details

### Market Hours Logic
- US market hours: 9:30 AM - 4:00 PM EST
- Automatic conversion to Beijing time for local operations
- Extended update intervals during non-market hours (24h on non-trading days)
- Trading day validation using exchange calendars with holiday support

### Trading Strategy Rules
- Tracks QQQ/SPY ratio (N) vs historical average (V)
- Position switching must go through CASH state (risk management)
- Includes RSI indicators for overbought/oversold confirmation
- Supports multiple ETFs and inverse ETFs for different market conditions
- Fear indicator provides additional context for extreme market conditions

### Fear Indicator Implementation
- VIX data fetched via Yahoo Finance (^VIX symbol)
- Fear score calculated from:
  - VIX percentile rank vs 1-year history
  - Current VIX level vs predefined thresholds
  - VIX trend direction (rising/falling/stable)
- Five fear levels with emojis for intuitive communication
- Historical VIX data stored for trend analysis and backtesting

### Error Handling Architecture
- Decorator-based pattern for consistent error handling across modules
- Specialized decorators for database operations and market data fetching
- Retry mechanisms with exponential backoff for API failures
- Graceful degradation when services are unavailable
- Comprehensive logging with contextual information

### Database Schema Evolution
- Recent addition of `vix_history` table for sentiment tracking
- All tables include timestamp fields for data freshness validation
- SQLite chosen for simplicity and reliability in single-instance deployment
- Automatic schema creation and initialization on first run

## Development Notes

### Dependencies
- Core: Python 3.8+, pandas, numpy, yfinance
- Time handling: pytz, python-dateutil, exchange-calendars
- HTTP: requests for notification APIs
- Configuration: python-dotenv

### Package Structure
- Main application code in `marketflow/` directory with clear module separation
- Configuration via `.env` (template in `.env.example`)
- Modern Python packaging with `pyproject.toml` for UV/pip compatibility
- Docker deployment ready with multi-stage builds
- Direct execution with UV for easy development and production deployment
- Data persistence in SQLite database (default: `data/investment.db`)
- Logs directory with proper permissions and volume mounting for Docker
- All constants centralized in `constants.py` for easy maintenance
- Development and production dependencies managed via `[project.optional-dependencies]`

### Working with Market Data
- The system implements intelligent caching to minimize API calls
- Weekly price updates occur automatically with freshness validation
- Real-time monitoring during market hours with extended intervals after hours
- Historical data stored for backtesting, analysis, and percentile calculations
- VIX data provides additional sentiment context beyond price action

### Extending the System
- Add new technical indicators in `market_data.py` following existing patterns
- Implement new strategies in `strategy.py` respecting the CASH state requirement
- Add notification channels in `notification.py` with retry mechanisms
- Extend database schema in `database.py` with proper initialization in `init_db()`
- New constants should be added to `constants.py` for centralization
- All new components should integrate with the error handling decorator system
- New dependencies should be added to `pyproject.toml` (maintaining `requirements.txt` for backward compatibility)
- Use `uv add <package>` for development dependency management