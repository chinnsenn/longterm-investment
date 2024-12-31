# MarketFlow

A sophisticated market trend following trading system that implements an adaptive QQQ/SPY rotation strategy based on their relative strength and moving averages.

[中文文档](README_cn.md)

## Features

- Real-time market data monitoring using Yahoo Finance API
- Dynamic QQQ/SPY rotation strategy
- Automated trading signals based on:
  - Relative strength ratio (QQQ/SPY)
  - Moving average indicators (QQQ MA30/MA50, SPY MA50/MA100)
  - Market trend confirmation
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
1. Relative strength comparison (QQQ/SPY ratio)
2. Moving average confirmations:
   - QQQ: 30-day and 50-day moving averages
   - SPY: 50-day and 100-day moving averages
3. Market trend validation

Notifications are sent through both Bark and Telegram when trading signals are generated.

## License

MIT License
