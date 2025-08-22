from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime
import numpy as np
from .market_data import MarketData
from .notification import Notifier
from .constants import SPY_MA40_WEEKS


class Position(Enum):
    CASH = "CASH"
    QQQ = "QQQ"
    SPY = "SPY"
    SH = "SH"  # Inverse S&P 500
    PSQ = "PSQ"  # Inverse NASDAQ 100
    AGG = "AGG"  # Bond ETF
    LQD = "LQD"  # Corporate Bond ETF
    TLT = "TLT"  # Treasury Bond ETF
    GLD = "GLD"  # Gold ETF


class TradingSignal:
    """Represents a trading signal with associated metadata."""
    
    def __init__(self, signal_type: str, message: str, position: Position):
        self.signal_type = signal_type
        self.message = message
        self.position = position
        self.timestamp = None


class Strategy:
    def __init__(self, threshold_value: float = 1.0, stop_loss_pct: float = 0.05):
        self.market_data = MarketData()
        self.notification = Notifier()
        self.threshold_value = threshold_value  # This is the V value in QQQ/SPY ratio
        self.stop_loss_pct = stop_loss_pct  # Stop loss percentage
        self.current_position: Optional[Position] = None
        self.last_switch_time: Optional[datetime] = None
        self.last_n_above_v: Optional[bool] = None  # Track the last N > V state
        self.entry_prices = {}  # Track entry prices for stop loss calculation
        
    def check_spy_ma_condition(self) -> bool:
        """Check if SPY is above its 40-week moving average."""
        spy_prices = self.market_data.get_weekly_prices("SPY", weeks=SPY_MA40_WEEKS)
        if not spy_prices:
            return False
        
        prices = list(spy_prices.values())
        ma_40 = np.mean(prices)
        current_price = prices[-1]
        
        return current_price > ma_40
    
    def _detect_crossover(self, current_n: float, v: float) -> tuple[bool, bool]:
        """
        Detect if N value crossed above or below V threshold.
        
        Returns:
            tuple[bool, bool]: (crossover_up, crossover_down)
        """
        current_n_above_v = current_n > v
        
        crossover_up = False
        crossover_down = False
        
        if self.last_n_above_v is not None:
            if not self.last_n_above_v and current_n_above_v:  # Upward crossover
                crossover_up = True
            elif self.last_n_above_v and not current_n_above_v:  # Downward crossover
                crossover_down = True
        
        self.last_n_above_v = current_n_above_v
        return crossover_up, crossover_down
    
    def _check_exit_conditions(self, crossover_up: bool, crossover_down: bool, 
                               spy_ma_condition: bool) -> Optional[Position]:
        """
        Check if we need to exit current position.
        
        Returns:
            Optional[Position]: Position to exit to (usually CASH), or None if no exit needed
        """
        # Exit QQQ if N crosses down below V
        if self.current_position == Position.QQQ and crossover_down:
            self._send_signal_notification("卖出QQQ信号", f"N下穿V，当前仓位: QQ")
            return Position.CASH
        
        # Exit SPY if N crosses above V OR SPY falls below 40-week MA
        if self.current_position == Position.SPY:
            if crossover_up:
                self._send_signal_notification("卖出SPY信号", f"N上穿V，当前仓位: SPY")
                return Position.CASH
            elif not spy_ma_condition:
                self._send_signal_notification("卖出SPY信号", f"SPY跌破40周均线，当前仓位: SPY")
                return Position.CASH
        
        return None
    
    def _check_entry_conditions(self, crossover_up: bool, crossover_down: bool,
                                current_n: float, v: float, spy_ma_condition: bool) -> Optional[Position]:
        """
        Check if we can enter a new position (only from CASH).
        
        Returns:
            Optional[Position]: Position to enter, or None if no entry signal
        """
        # Can only enter from CASH
        if self.current_position != Position.CASH:
            return None
        
        # Enter QQQ on upward crossover
        if crossover_up:
            self._send_signal_notification("买入QQQ信号", f"N上穿V，比值: {current_n:.4f}, 阈值: {v:.4f}")
            return Position.QQQ
        
        # Enter SPY if N ≤ V AND SPY > 40-week MA
        if current_n <= v and spy_ma_condition:
            self._send_signal_notification("买入SPY信号", f"N≤V且SPY>40MA，比值: {current_n:.4f}, 阈值: {v:.4f}")
            return Position.SPY
        
        return None
    
    def _send_signal_notification(self, title: str, message: str):
        """Send a trading signal notification."""
        self.notification.send_bark_notification(title, message)
    
    def evaluate_position(self, current_n: float, v: float, spy_ma_condition: bool) -> Position:
        """
        Evaluate market conditions and determine the optimal position.
        
        Args:
            current_n: Current QQQ/SPY ratio
            v: Threshold value
            spy_ma_condition: Whether SPY is above its 40-week MA
            
        Returns:
            Position: The recommended position (CASH, QQQ, or SPY)
        """
        # Detect crossovers
        crossover_up, crossover_down = self._detect_crossover(current_n, v)
        
        # Send crossover notifications
        if crossover_up:
            self._send_signal_notification("N上穿V", f"比值: {current_n:.4f}, 阈值: {v:.4f}")
        elif crossover_down:
            self._send_signal_notification("N下穿V", f"比值: {current_n:.4f}, 阈值: {v:.4f}")
        
        # Check exit conditions first
        exit_position = self._check_exit_conditions(crossover_up, crossover_down, spy_ma_condition)
        if exit_position:
            return exit_position
        
        # Check entry conditions
        entry_position = self._check_entry_conditions(crossover_up, crossover_down, 
                                                     current_n, v, spy_ma_condition)
        if entry_position:
            return entry_position
        
        # Keep current position
        return self.current_position or Position.CASH
    
    def evaluate_position_enhanced(self, current_n: float, v: float, 
                                  spy_ma_condition: bool, qqq_rsi: float, 
                                  spy_rsi: float, qqq_ma_trend: str, 
                                  spy_ma_trend: str, fear_score: float) -> Position:
        """
        Enhanced position evaluation with multi-factor confirmation.
        
        Args:
            current_n: Current QQQ/SPY ratio
            v: Threshold value
            spy_ma_condition: Whether SPY is above its 40-week MA
            qqq_rsi: QQQ RSI value
            spy_rsi: SPY RSI value
            qqq_ma_trend: QQQ moving average trend
            spy_ma_trend: SPY moving average trend
            fear_score: Market fear score (0-100)
            
        Returns:
            Position: The recommended position
        """
        # Detect crossovers
        crossover_up, crossover_down = self._detect_crossover(current_n, v)
        
        # Multi-factor confirmation logic
        qqq_entry_confirmed = (
            crossover_up and 
            qqq_rsi < 70 and  # Not overbought
            qqq_ma_trend == 'rising' and  # QQQ trend is up
            fear_score < 70  # Not extremely greedy
        )
        
        spy_entry_confirmed = (
            current_n <= v and 
            spy_ma_condition and
            spy_rsi < 70 and  # Not overbought
            spy_ma_trend == 'rising' and  # SPY trend is up
            fear_score > 30  # Not extremely fearful
        )
        
        # Exit conditions with multi-factor confirmation
        qqq_exit_confirmed = (
            crossover_down or 
            qqq_rsi > 80 or  # Overbought
            qqq_ma_trend == 'falling' or  # Trend down
            fear_score > 80  # Extremely greedy
        )
        
        spy_exit_confirmed = (
            (crossover_up and fear_score > 50) or  # Don't switch in fearful environment
            (not spy_ma_condition) or
            spy_rsi > 80 or  # Overbought
            spy_ma_trend == 'falling' or  # Trend down
            fear_score > 80  # Extremely greedy
        )
        
        # Decision based on multi-factor confirmation
        if self.current_position == Position.QQQ and qqq_exit_confirmed:
            self._send_signal_notification("卖出QQQ信号", f"多因子确认卖出: N下穿V或超买或趋势向下")
            # Record exit price for stop loss calculation
            if 'QQQ' in self.entry_prices:
                del self.entry_prices['QQQ']
            return Position.CASH
        elif self.current_position == Position.SPY and spy_exit_confirmed:
            self._send_signal_notification("卖出SPY信号", f"多因子确认卖出: 条件不满足或超买或趋势向下")
            # Record exit price for stop loss calculation
            if 'SPY' in self.entry_prices:
                del self.entry_prices['SPY']
            return Position.CASH
        elif self.current_position == Position.CASH:
            if qqq_entry_confirmed:
                self._send_signal_notification("买入QQQ信号", f"多因子确认买入: N上穿V且趋势向上")
                return Position.QQQ
            elif spy_entry_confirmed:
                self._send_signal_notification("买入SPY信号", f"多因子确认买入: N≤V且SPY趋势向上")
                return Position.SPY
        
        return self.current_position or Position.CASH
    
    def check_stop_loss(self, current_positions: Dict[str, float], 
                       current_prices: Dict[str, float]) -> List[str]:
        """
        Check if stop loss is triggered for any positions.
        
        Args:
            current_positions: Current positions
            current_prices: Current market prices
            
        Returns:
            List of symbols that triggered stop loss
        """
        stop_loss_symbols = []
        for symbol, entry_price in self.entry_prices.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                loss_pct = (entry_price - current_price) / entry_price
                if loss_pct >= self.stop_loss_pct:
                    stop_loss_symbols.append(symbol)
        return stop_loss_symbols
    
    def update_entry_price(self, symbol: str, price: float):
        """
        Update entry price for a symbol.
        
        Args:
            symbol: The symbol
            price: Entry price
        """
        self.entry_prices[symbol] = price