# MarketFlow

A sophisticated market trend following trading system that implements an adaptive QQQ/SPY rotation strategy based on their relative strength and moving averages.

## Features

- Real-time market data monitoring using Yahoo Finance API
- Dynamic QQQ/SPY rotation strategy
- Automated trading signals based on:
  - Relative strength ratio (QQQ/SPY)
  - Moving average crossovers
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

## Configuration

The system can be configured through the `.env` file:
- `BARK_API_KEY`: Your Bark API key for notifications
- `BARK_URL`: Bark server URL
- `DB_PATH`: Path to the SQLite database
- `RETRY_INTERVAL`: Retry interval for failed operations
- Other optional settings (see `.env.example`)

## License

MIT License
