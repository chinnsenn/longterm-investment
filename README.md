# MarketFlow

A sophisticated market trend following trading system that implements an adaptive QQQ/SPY rotation strategy based on their relative strength and moving averages.

[中文文档](README_cn.md)

## Features

- Real-time market data monitoring using Yahoo Finance API
- Dynamic QQQ/SPY rotation strategy
- Automated trading signals based on:
  - Relative strength ratio (QQQ/SPY)
  - Moving average indicators (QQQ MA30/MA50, SPY MA50/MA100)
  - RSI overbought/oversold indicators
  - Market trend confirmation
- **Market Fear Indicator**: VIX-based market sentiment analysis
  - Real-time VIX data fetching and historical percentile analysis
  - Five-level fear gauge: Extreme Fear, Fear, Neutral, Greed, Extreme Greed
  - VIX trend analysis and fear scoring (0-100)
- Multiple notification channels (Bark, Telegram)
- Robust error handling and retry mechanisms
- Efficient data caching and storage
- Smart update intervals based on market hours

## Installation

1. Clone the repository:
```bash
git clone git@github.com:chinnsenn/longterm-investment.git
cd longterm-investment
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

Run the main application:
```bash
python main.py
```

## Docker Deployment

### Using Docker

1. Build the Docker image:
```bash
docker build -t marketflow .
```

2. Run the container:
```bash
docker run -d \
  --name marketflow \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  marketflow
```

3. View logs:
```bash
docker logs -f marketflow
```

### Using Docker Compose

1. Start the application:
```bash
docker compose up -d
```

2. View logs:
```bash
docker compose logs -f
```

3. Stop the application:
```bash
docker compose down
```

Note: Make sure to configure your `.env` file before building the Docker image.

## Configuration

The system can be configured through the `.env` file:
- `BARK_API_KEY`: Your Bark API key for notifications
- `BARK_URL`: Bark server URL
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `DB_PATH`: Path to the SQLite database
- `RETRY_INTERVAL`: Retry interval for failed operations
- Other optional settings (see `.env.example`)

## Strategy Details

The system implements a sophisticated rotation strategy between QQQ and SPY based on:

### Core Strategy Components
1. **Relative Strength Analysis**: Calculates and monitors QQQ/SPY ratio
2. **Technical Indicator Confirmations**:
   - Moving Averages: QQQ MA30/MA50, SPY MA50/MA100
   - RSI Indicators: Identifies overbought/oversold conditions
   - Trend Confirmation: Ensures signal reliability
3. **Market Sentiment Analysis**:
   - Real-time VIX fear gauge monitoring
   - Historical percentile comparison
   - Fear level assessment (Extreme Fear to Extreme Greed)

### Trading Logic
- Favors QQQ when QQQ/SPY ratio exceeds threshold
- Favors SPY when ratio is below threshold AND SPY is above 40-week MA
- Must pass through CASH state when switching positions
- Uses fear indicator as supplementary analysis for market extremes

### Notification System
When trading signals are generated or market sentiment changes, the system sends notifications via both Bark and Telegram containing:
- Strategy recommendations and position status
- Technical indicator details
- Market fear index and sentiment analysis

## License

MIT License
