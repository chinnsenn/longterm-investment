from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime
import numpy as np
from .market_data import MarketData
from .notification import Notifier

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

class Strategy:
    def __init__(self, threshold_value: float = 1.0):
        self.market_data = MarketData()
        self.notification = Notifier()
        self.threshold_value = threshold_value  # This is the V value in QQQ/SPY ratio
        self.current_position: Optional[Position] = None
        self.last_switch_time: Optional[datetime] = None
        self.last_n_above_v: Optional[bool] = None  # Track the last N > V state
        
    def can_switch_position(self, from_pos: Position, to_pos: Position) -> bool:
        """
        Enforce switching rules:
        - Can only switch between CASH and QQQ (1-3)
        - Can only switch between CASH and SPY (2-3)
        - Cannot directly switch between QQQ and SPY
        """
        if from_pos == Position.CASH:
            return True  # Can switch from CASH to any position
        elif from_pos == Position.QQQ:
            return to_pos == Position.CASH  # Can only switch from QQQ to CASH
        elif from_pos == Position.SPY:
            return to_pos == Position.CASH  # Can only switch from SPY to CASH
        return False
        
    def calculate_ratio(self) -> float:
        """Calculate the QQQ/SPY ratio using latest prices."""
        qqq_price = self.market_data.get_latest_price("QQQ")
        spy_price = self.market_data.get_latest_price("SPY")
        if not spy_price:
            self.notification.send_bark_notification("警告: SPY价格为0，无法计算比值", "数据获取失败")
            return 0.0
        ratio = qqq_price / spy_price
        self.notification.send_bark_notification(f"计算QQQ/SPY比值: {ratio:.1f}", "比值计算结果")
        return ratio
    
    def check_spy_ma_condition(self) -> bool:
        """Check if SPY is above its 40-week moving average."""
        spy_prices = self.market_data.get_weekly_prices("SPY", weeks=40)
        if not spy_prices:
            self.notification.send_bark_notification("警告: 无法获取SPY价格数据", "数据获取失败")
            return False
        
        prices = list(spy_prices.values())
        ma_40 = np.mean(prices)
        current_price = prices[-1]
        
        is_above_ma = current_price > ma_40
        message = (
            f"SPY价格: ${current_price:.2f}\n"
            f"40周均线: ${ma_40:.2f}\n"
            f"差值: ${(current_price - ma_40):.2f}"
        )
        self.notification.send_bark_notification(
            message,
            "SPY多头信号" if is_above_ma else "SPY空头信号"
        )
        return is_above_ma
    
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
        current_n_above_v = current_n > v
        
        # 检查是否发生了上穿或下穿
        n_crossover_up = False
        n_crossover_down = False
        if self.last_n_above_v is not None:
            if not self.last_n_above_v and current_n_above_v:  # 上穿
                n_crossover_up = True
                self.notification.send_bark_notification(
                    f"N上穿V",
                    f"比值: {current_n:.4f}, 阈值: {v:.4f}"
                )
            elif self.last_n_above_v and not current_n_above_v:  # 下穿
                n_crossover_down = True
                self.notification.send_bark_notification(
                    f"N下穿V",
                    f"比值: {current_n:.4f}, 阈值: {v:.4f}"
                )
        self.last_n_above_v = current_n_above_v
        
        # 检查SPY的MA条件变化
        if self.current_position == Position.SPY and not spy_ma_condition:
            # 如果持有SPY且跌破40周线，必须卖出
            self.notification.send_bark_notification(
                f"卖出SPY信号",
                f"SPY跌破40周均线，N/V比值: {current_n:.4f}"
            )
            return Position.CASH
        
        # 如果当前持有QQQ，且N下穿V，必须先卖出
        if self.current_position == Position.QQQ and n_crossover_down:
            self.notification.send_bark_notification(
                f"卖出QQQ信号",
                f"N下穿V，比值: {current_n:.4f}, 阈值: {v:.4f}"
            )
            return Position.CASH
            
        # 如果当前持有SPY，且N上穿V，必须先卖出
        if self.current_position == Position.SPY and n_crossover_up:
            self.notification.send_bark_notification(
                f"卖出SPY信号",
                f"N上穿V，比值: {current_n:.4f}, 阈值: {v:.4f}"
            )
            return Position.CASH
            
        # 只有在现金状态下才考虑新的入场信号
        if self.current_position == Position.CASH:
            # 策略1：N上穿V时买入QQQ
            if n_crossover_up:
                self.notification.send_bark_notification(
                    f"买入QQQ信号",
                    f"N上穿V，比值: {current_n:.4f}, 阈值: {v:.4f}"
                )
                return Position.QQQ
                
            # 策略2：N≤V且SPY>40MA时买入SPY
            if current_n <= v and spy_ma_condition:
                self.notification.send_bark_notification(
                    f"买入SPY信号",
                    f"N≤V且SPY>40MA，比值: {current_n:.4f}, 阈值: {v:.4f}"
                )
                return Position.SPY
        
        # 保持当前仓位
        return self.current_position or Position.CASH

    def get_alternative_positions(self) -> List[Position]:
        """Get list of alternative positions after selling."""
        return [
            Position.CASH,
            Position.SH,
            Position.PSQ,
            Position.AGG,
            Position.LQD,
            Position.TLT,
            Position.GLD
        ]
    
    def update(self) -> Optional[Position]:
        """Update strategy and return new position if change is needed."""
        ratio = self.calculate_ratio()
        spy_ma_condition = self.check_spy_ma_condition()
        new_position = self.evaluate_position(ratio, self.threshold_value, spy_ma_condition)
        
        if new_position != self.current_position:
            self.current_position = new_position
            return new_position
            
        return None
