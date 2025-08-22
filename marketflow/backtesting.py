"""
Backtesting framework for MarketFlow strategies.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from marketflow.strategy import Strategy, Position
from marketflow.market_data import MarketData
from marketflow.ratio_calculator import QQQSPYRatioCalculator
from marketflow.database import DatabaseManager


class Backtester:
    """Backtesting framework for trading strategies."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.market_data = MarketData()
        self.results = []
        
    def load_historical_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for backtesting.
        
        Args:
            symbols: List of symbols to load data for
            
        Returns:
            Dictionary mapping symbols to DataFrames with historical data
        """
        historical_data = {}
        for symbol in symbols:
            try:
                ticker = self.market_data._get_ticker(symbol)
                df = ticker.history(start=self.start_date, end=self.end_date)
                historical_data[symbol] = df
            except Exception as e:
                print(f"Error loading data for {symbol}: {str(e)}")
        return historical_data
        
    def run_backtest(self, strategy: Strategy, historical_data: Dict[str, pd.DataFrame]) -> Dict[str, any]:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy instance to test
            historical_data: Historical data for symbols
            
        Returns:
            Dictionary with backtest results
        """
        # Initialize backtest parameters
        portfolio_value = 100000  # Initial capital of $100,000
        position = Position.CASH
        position_size = 0
        trades = []
        daily_values = []
        
        # Get data for QQQ and SPY
        qqq_data = historical_data.get('QQQ')
        spy_data = historical_data.get('SPY')
        
        if qqq_data is None or spy_data is None:
            raise ValueError("Missing required historical data for QQQ or SPY")
            
        # Align dates
        common_dates = qqq_data.index.intersection(spy_data.index)
        qqq_data = qqq_data.loc[common_dates]
        spy_data = spy_data.loc[common_dates]
        
        # Calculate historical ratios and thresholds
        ratios = qqq_data['Close'] / spy_data['Close']
        v_values = ratios.rolling(window=10).mean()  # 10-period moving average as threshold
        
        # Start backtest loop
        for i in range(10, len(common_dates)):  # Skip first 10 data points for sufficient history
            date = common_dates[i]
            current_qqq = qqq_data.loc[date, 'Close']
            current_spy = spy_data.loc[date, 'Close']
            current_ratio = ratios.loc[date]
            current_v = v_values.loc[date]
            
            # Calculate SPY 40-week MA condition (simplified to 200-day MA)
            spy_ma_condition = current_spy > spy_data['Close'].rolling(window=200).mean().loc[date]
            
            # Save current position
            previous_position = position
            
            # Strategy decision
            position = strategy.evaluate_position(current_ratio, current_v, spy_ma_condition)
            
            # Record trades
            if position != previous_position:
                trade = {
                    'date': date,
                    'action': position.value,
                    'from': previous_position.value,
                    'ratio': current_ratio,
                    'threshold': current_v,
                    'qqq_price': current_qqq,
                    'spy_price': current_spy
                }
                trades.append(trade)
                
                # Update position size
                if position == Position.QQQ:
                    position_size = portfolio_value / current_qqq
                elif position == Position.SPY:
                    position_size = portfolio_value / current_spy
                else:
                    position_size = 0
                    
            # Calculate daily value
            if position == Position.QQQ:
                daily_value = position_size * current_qqq
            elif position == Position.SPY:
                daily_value = position_size * current_spy
            else:
                daily_value = portfolio_value
                
            daily_values.append({
                'date': date,
                'value': daily_value,
                'position': position.value
            })
            
            # Update portfolio value
            portfolio_value = daily_value
            
        # Calculate backtest results
        initial_value = 100000
        final_value = daily_values[-1]['value'] if daily_values else initial_value
        total_return = (final_value - initial_value) / initial_value
        
        # Calculate annualized return
        years = (self.end_date - self.start_date).days / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # Calculate maximum drawdown
        values = [dv['value'] for dv in daily_values]
        peak = np.maximum.accumulate(values)
        drawdown = (peak - values) / peak
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Calculate Sharpe ratio (assuming risk-free rate of 2%)
        returns = np.diff(values) / values[:-1] if len(values) > 1 else [0]
        risk_free_rate = 0.02
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        sharpe_ratio = np.mean(excess_returns) / (np.std(excess_returns) + 1e-8) * np.sqrt(252)
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades': trades,
            'daily_values': daily_values,
            'initial_value': initial_value,
            'final_value': final_value
        }
        
    def optimize_parameters(self, param_ranges: Dict[str, Tuple[float, float, int]]) -> Dict[str, any]:
        """
        Optimize strategy parameters.
        
        Args:
            param_ranges: Dictionary mapping parameter names to (start, end, steps) tuples
            
        Returns:
            Dictionary with best parameters and performance
        """
        best_params = {}
        best_performance = {'sharpe_ratio': -np.inf}
        
        # Grid search parameter optimization
        param_combinations = self._generate_param_combinations(param_ranges)
        
        for params in param_combinations:
            # Create strategy instance
            strategy = Strategy(threshold_value=params.get('threshold_value', 1.0))
            
            # Run backtest
            try:
                results = self.run_backtest(strategy, self.historical_data)
                if results['sharpe_ratio'] > best_performance['sharpe_ratio']:
                    best_performance = results
                    best_params = params
            except Exception as e:
                print(f"Error testing parameters {params}: {str(e)}")
                continue
                
        return {
            'best_params': best_params,
            'best_performance': best_performance
        }
        
    def _generate_param_combinations(self, param_ranges: Dict[str, Tuple[float, float, int]]) -> List[Dict[str, float]]:
        """
        Generate parameter combinations for grid search.
        
        Args:
            param_ranges: Dictionary mapping parameter names to (start, end, steps) tuples
            
        Returns:
            List of parameter dictionaries
        """
        import itertools
        
        param_lists = []
        param_names = []
        
        for param_name, (start, end, steps) in param_ranges.items():
            param_values = np.linspace(start, end, steps)
            param_lists.append(param_values)
            param_names.append(param_name)
            
        # Generate all combinations
        combinations = list(itertools.product(*param_lists))
        param_combinations = []
        
        for combo in combinations:
            param_dict = {}
            for i, param_name in enumerate(param_names):
                param_dict[param_name] = combo[i]
            param_combinations.append(param_dict)
            
        return param_combinations


class PerformanceAnalyzer:
    """Analyzer for backtest performance metrics."""
    
    @staticmethod
    def calculate_performance_metrics(daily_values: List[Dict]) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            daily_values: List of daily portfolio values
            
        Returns:
            Dictionary with performance metrics
        """
        if not daily_values:
            return {}
            
        values = [dv['value'] for dv in daily_values]
        dates = [dv['date'] for dv in daily_values]
        
        # Basic metrics
        initial_value = values[0]
        final_value = values[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # Volatility
        returns = np.diff(values) / values[:-1] if len(values) > 1 else [0]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
        
        # Maximum drawdown
        peak = np.maximum.accumulate(values)
        drawdown = (peak - values) / peak
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        sharpe_ratio = np.mean(excess_returns) / (np.std(excess_returns) + 1e-8) * np.sqrt(252)
        
        # Sortino ratio (downside risk)
        negative_returns = [r for r in excess_returns if r < 0]
        downside_deviation = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
        sortino_ratio = np.mean(excess_returns) / (downside_deviation + 1e-8) * np.sqrt(252) if downside_deviation > 0 else 0
        
        # Calmar ratio
        calmar_ratio = abs(total_return) / (max_drawdown + 1e-8) if max_drawdown > 0 else 0
        
        # Win rate
        positive_periods = sum(1 for r in returns if r > 0)
        win_rate = positive_periods / len(returns) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': total_return * 252 / len(returns) if len(returns) > 0 else 0,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'initial_value': initial_value,
            'final_value': final_value
        }
        
    @staticmethod
    def compare_with_benchmark(strategy_returns: List[float], benchmark_returns: List[float]) -> Dict[str, float]:
        """
        Compare strategy performance with benchmark.
        
        Args:
            strategy_returns: List of strategy returns
            benchmark_returns: List of benchmark returns
            
        Returns:
            Dictionary with comparison metrics
        """
        if len(strategy_returns) != len(benchmark_returns):
            raise ValueError("Strategy and benchmark returns must have the same length")
            
        # Alpha and beta calculation
        covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / (benchmark_variance + 1e-8)
        
        strategy_mean = np.mean(strategy_returns)
        benchmark_mean = np.mean(benchmark_returns)
        alpha = strategy_mean - beta * benchmark_mean
        
        # Tracking error
        tracking_error = np.std(np.array(strategy_returns) - np.array(benchmark_returns))
        
        # Information ratio
        information_ratio = alpha / (tracking_error + 1e-8) if tracking_error > 0 else 0
        
        return {
            'alpha': alpha,
            'beta': beta,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio
        }