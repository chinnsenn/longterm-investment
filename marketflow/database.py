"""Database operations for storing and retrieving market data."""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .error_handling import handle_database_errors


class DatabaseManager:
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db_path = db_path
        self.init_db()
    
    @handle_database_errors
    def init_db(self):
        """Initialize database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_prices (
                    date TEXT,
                    symbol TEXT,
                    price REAL,
                    last_updated TEXT,
                    PRIMARY KEY (date, symbol)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calculations (
                    date TEXT PRIMARY KEY,
                    n_values TEXT,
                    v_value REAL,
                    last_updated TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_n_above_v BOOLEAN,
                    last_check_time TEXT,
                    last_long_signal TEXT,
                    last_signal_time TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vix_history (
                    date TEXT PRIMARY KEY,
                    vix_value REAL,
                    vix_percentile REAL,
                    fear_score REAL,
                    fear_level TEXT,
                    last_updated TEXT
                )
            ''')
            
            # Initialize signal state if not exists
            cursor.execute('''
                INSERT OR IGNORE INTO signal_state (id, last_n_above_v, last_check_time, last_long_signal, last_signal_time)
                VALUES (1, 0, datetime('now'), NULL, NULL)
            ''')
            
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            # Provide more detailed error information for permission issues
            if "unable to open database file" in str(e):
                raise sqlite3.OperationalError(
                    f"Unable to open database file at {self.db_path}. "
                    f"This is likely a permissions issue. Please ensure the directory is writable by the application. "
                    f"Error details: {str(e)}"
                ) from e
            else:
                raise
    
    @handle_database_errors
    def is_data_fresh(self, max_age_hours: int = 24) -> bool:
        """Check if the cached data is fresh (updated within max_age_hours)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check weekly_prices table
        cursor.execute('''
            SELECT last_updated FROM weekly_prices
            ORDER BY last_updated DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
            
        last_updated = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
        age = datetime.now() - last_updated
        
        return age.total_seconds() < (max_age_hours * 3600)
    
    @handle_database_errors
    def store_weekly_prices(self, prices: Dict[datetime, float], symbol: str):
        """Store weekly prices for a symbol."""
        if not prices:
            raise ValueError("Empty price data")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for date, price in prices.items():
            cursor.execute('''
                INSERT OR REPLACE INTO weekly_prices (date, symbol, price, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (date.strftime('%Y-%m-%d'), symbol, price, current_time))
        
        conn.commit()
        conn.close()
    
    @handle_database_errors
    def store_calculations(self, n_values: List[float], v_value: float):
        """Store N values and V calculation."""
        if not n_values or v_value is None:
            raise ValueError("Invalid calculation data")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        n_values_str = ','.join(map(str, n_values))
        
        cursor.execute('''
            INSERT OR REPLACE INTO calculations (date, n_values, v_value, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (current_date, n_values_str, v_value, current_time))
        
        conn.commit()
        conn.close()
    
    @handle_database_errors
    def get_latest_v_value(self) -> Optional[float]:
        """Get the latest V value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v_value FROM calculations
            ORDER BY date DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    @handle_database_errors
    def has_data(self) -> bool:
        """Check if there is any data in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check weekly_prices table
        cursor.execute('''
            SELECT COUNT(*) FROM weekly_prices
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] > 0
    
    @handle_database_errors
    def store_vix_data(self, vix_value: float, vix_percentile: float, fear_score: float, fear_level: str):
        """Store VIX data and fear indicators."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT OR REPLACE INTO vix_history (date, vix_value, vix_percentile, fear_score, fear_level, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_date, vix_value, vix_percentile, fear_score, fear_level, current_time))
        
        conn.commit()
        conn.close()
    
    @handle_database_errors
    def get_vix_history(self, days: int = 30) -> list:
        """Get recent VIX history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT date, vix_value, vix_percentile, fear_score, fear_level
            FROM vix_history
            WHERE date >= ?
            ORDER BY date DESC
        ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'vix_value': row[1],
                'vix_percentile': row[2],
                'fear_score': row[3],
                'fear_level': row[4]
            }
            for row in results
        ]
    
    @handle_database_errors
    def get_latest_vix_data(self) -> Optional[dict]:
        """Get the latest VIX data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vix_value, vix_percentile, fear_score, fear_level, last_updated
            FROM vix_history
            ORDER BY date DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'vix_value': result[0],
                'vix_percentile': result[1],
                'fear_score': result[2],
                'fear_level': result[3],
                'last_updated': result[4]
            }
        return None