"""
Risk management module for MarketFlow.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .strategy import Position


class TransactionCostModel:
    """Model for calculating transaction costs."""
    
    def __init__(self, commission_rate: float = 0.001, slippage_rate: float = 0.0005):
        """
        Initialize transaction cost model.
        
        Args:
            commission_rate: Commission rate per trade (default: 0.1%)
            slippage_rate: Slippage rate per trade (default: 0.05%)
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        
    def calculate_total_cost(self, trade_value: float, trade_type: str = 'buy') -> float:
        """
        Calculate total transaction cost.
        
        Args:
            trade_value: Value of the trade
            trade_type: Type of trade ('buy' or 'sell')
            
        Returns:
            Total transaction cost
        """
        commission = trade_value * self.commission_rate
        slippage = trade_value * self.slippage_rate
        return commission + slippage
        
    def adjust_for_costs(self, expected_return: float, trade_value: float) -> float:
        """
        Adjust expected return for transaction costs.
        
        Args:
            expected_return: Expected return before costs
            trade_value: Value of the trade
            
        Returns:
            Net expected return after costs
        """
        total_cost = self.calculate_total_cost(trade_value)
        return expected_return - total_cost


class PositionSizer:
    """Position sizing calculator using various methods."""
    
    def __init__(self, account_value: float = 100000.0):
        """
        Initialize position sizer.
        
        Args:
            account_value: Total account value for position sizing
        """
        self.account_value = account_value
        
    def calculate_kelly_criterion(self, win_rate: float, profit_loss_ratio: float) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0-1)
            profit_loss_ratio: Average profit/loss ratio
            
        Returns:
            Kelly fraction (0-1)
        """
        if win_rate <= 0 or profit_loss_ratio <= 0:
            return 0.0
            
        kelly_fraction = win_rate - (1 - win_rate) / profit_loss_ratio
        # Limit to maximum 25% of account
        return min(kelly_fraction, 0.25)
        
    def calculate_fixed_fraction(self, risk_per_trade: float = 0.01) -> float:
        """
        Calculate position size using fixed fraction method.
        
        Args:
            risk_per_trade: Fraction of account to risk per trade (default: 1%)
            
        Returns:
            Position size as fraction of account (0-1)
        """
        return risk_per_trade
        
    def calculate_volatility_adjusted(self, volatility: float, risk_per_trade: float = 0.01) -> float:
        """
        Calculate position size adjusted for volatility.
        
        Args:
            volatility: Asset volatility
            risk_per_trade: Fraction of account to risk per trade
            
        Returns:
            Position size as fraction of account (0-1)
        """
        if volatility <= 0:
            return risk_per_trade
            
        # Reduce position size as volatility increases
        adjusted_risk = risk_per_trade / (1 + volatility)
        return max(adjusted_risk, risk_per_trade * 0.1)  # Minimum 10% of base risk


class DrawdownController:
    """Drawdown control and monitoring."""
    
    def __init__(self, max_allowed_drawdown: float = 0.20):
        """
        Initialize drawdown controller.
        
        Args:
            max_allowed_drawdown: Maximum allowed drawdown (default: 20%)
        """
        self.max_allowed_drawdown = max_allowed_drawdown
        self.peak_value = 0.0
        self.current_value = 0.0
        
    def update_portfolio_value(self, portfolio_value: float) -> bool:
        """
        Update portfolio value and check drawdown.
        
        Args:
            portfolio_value: Current portfolio value
            
        Returns:
            True if drawdown exceeds maximum allowed, False otherwise
        """
        self.current_value = portfolio_value
        
        # Update peak value
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
            
        # Check drawdown
        if self.peak_value > 0:
            current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
            return current_drawdown >= self.max_allowed_drawdown
            
        return False
        
    def get_current_drawdown(self) -> float:
        """
        Get current drawdown.
        
        Returns:
            Current drawdown as fraction (0-1)
        """
        if self.peak_value > 0:
            return (self.peak_value - self.current_value) / self.peak_value
        return 0.0


class RiskMetrics:
    """Calculate and track various risk metrics."""
    
    def __init__(self, lookback_period: int = 252):
        """
        Initialize risk metrics calculator.
        
        Args:
            lookback_period: Number of periods for calculating metrics (default: 252 trading days)
        """
        self.lookback_period = lookback_period
        self.returns_history = []
        
    def add_return(self, return_value: float):
        """
        Add a return value to history.
        
        Args:
            return_value: Return for the period
        """
        self.returns_history.append(return_value)
        # Keep only the last lookback_period returns
        if len(self.returns_history) > self.lookback_period:
            self.returns_history.pop(0)
            
    def calculate_volatility(self) -> float:
        """
        Calculate annualized volatility.
        
        Returns:
            Annualized volatility
        """
        if len(self.returns_history) < 2:
            return 0.0
            
        return np.std(self.returns_history) * np.sqrt(252)
        
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
            
        Returns:
            Sharpe ratio
        """
        if len(self.returns_history) < 2:
            return 0.0
            
        mean_return = np.mean(self.returns_history) * 252  # Annualize
        volatility = self.calculate_volatility()
        
        if volatility == 0:
            return 0.0
            
        return (mean_return - risk_free_rate) / volatility
        
    def calculate_value_at_risk(self, confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            confidence_level: Confidence level for VaR (default: 5%)
            
        Returns:
            Value at Risk
        """
        if len(self.returns_history) < 10:
            return 0.0
            
        # Calculate VaR using historical simulation
        sorted_returns = np.sort(self.returns_history)
        var_index = int(len(sorted_returns) * confidence_level)
        return abs(sorted_returns[var_index])
        
    def calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown from returns history.
        
        Returns:
            Maximum drawdown
        """
        if len(self.returns_history) < 2:
            return 0.0
            
        # Calculate cumulative returns
        cumulative_returns = [1.0]
        for ret in self.returns_history:
            cumulative_returns.append(cumulative_returns[-1] * (1 + ret))
            
        # Calculate drawdowns
        peak = np.maximum.accumulate(cumulative_returns)
        drawdowns = (peak - cumulative_returns) / peak
        return np.max(drawdowns)


class StopLossManager:
    """Stop loss management for positions."""
    
    def __init__(self, stop_loss_pct: float = 0.05, trailing_stop: bool = True):
        """
        Initialize stop loss manager.
        
        Args:
            stop_loss_pct: Stop loss percentage (default: 5%)
            trailing_stop: Whether to use trailing stop (default: True)
        """
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop = trailing_stop
        self.entry_prices = {}
        self.trailing_prices = {}
        
    def set_stop_loss(self, symbol: str, entry_price: float):
        """
        Set stop loss for a position.
        
        Args:
            symbol: Symbol for the position
            entry_price: Entry price for the position
        """
        self.entry_prices[symbol] = entry_price
        if self.trailing_stop:
            self.trailing_prices[symbol] = entry_price
            
    def update_trailing_stop(self, symbol: str, current_price: float):
        """
        Update trailing stop price.
        
        Args:
            symbol: Symbol for the position
            current_price: Current market price
        """
        if self.trailing_stop and symbol in self.trailing_prices:
            # Move stop loss up if price increases
            if current_price > self.trailing_prices[symbol]:
                self.trailing_prices[symbol] = current_price
                
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss is triggered.
        
        Args:
            symbol: Symbol for the position
            current_price: Current market price
            
        Returns:
            True if stop loss is triggered, False otherwise
        """
        if symbol not in self.entry_prices:
            return False
            
        entry_price = self.entry_prices[symbol]
        
        # Use trailing stop price if applicable
        stop_price = entry_price * (1 - self.stop_loss_pct)
        if self.trailing_stop and symbol in self.trailing_prices:
            trailing_stop_price = self.trailing_prices[symbol] * (1 - self.stop_loss_pct)
            stop_price = max(stop_price, trailing_stop_price)
            
        return current_price <= stop_price
        
    def get_stop_loss_price(self, symbol: str) -> Optional[float]:
        """
        Get current stop loss price for a symbol.
        
        Args:
            symbol: Symbol for the position
            
        Returns:
            Stop loss price or None if not set
        """
        if symbol not in self.entry_prices:
            return None
            
        entry_price = self.entry_prices[symbol]
        stop_price = entry_price * (1 - self.stop_loss_pct)
        
        if self.trailing_stop and symbol in self.trailing_prices:
            trailing_stop_price = self.trailing_prices[symbol] * (1 - self.stop_loss_pct)
            stop_price = max(stop_price, trailing_stop_price)
            
        return stop_price