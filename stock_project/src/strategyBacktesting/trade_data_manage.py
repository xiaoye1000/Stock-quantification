import pandas as pd

#数据库
from ..SQLbase.SQLite_manage import (
    query_trade_table
)

"""
股票持仓管理类，用于跟踪单只股票的持仓状态和收益变化
"""
class StockPosition:
    #构造函数
    def __init__(self, table_name: str):
        """
        参数:
        trade_data -- 交易数据DataFrame，需包含字段：
            trade_date: 交易日期 (str)
            code: 股票代码 (str)
            trade_price: 交易价格 (float)
            trade_number: 交易数量 (float)
            isbuy: 是否买入 (1=买入, 0=卖出)
        """

        # 从数据库获取交易数据
        try:
            self.trade_data = query_trade_table(table_name)
        except Exception as e:
            raise RuntimeError(f"数据库查询失败: {str(e)}") from e

        # 检查数据是否为空
        if not hasattr(self.trade_data, 'empty') or self.trade_data.empty:
            raise ValueError(f"表 '{table_name}' 中无有效交易数据，检查输入表名是否正确")

        # 从第一条交易记录获取股票基本信息
        first_trade = self.trade_data.iloc[0]
        self.stock_code = first_trade['code']
        self.stock_name = first_trade['code_name']

        # 动态状态
        self.current_shares = 0.0       # 当前持仓数量
        self.total_investment = 0.0     # 当前持仓总金额（买入总金额 - 卖出总金额）
        self.average_cost = 0.0         # 当前持仓成本（总金额/持仓数量）
        self.realized_profit = 0.0      # 累计实现收益（卖出收益）

        # 历史记录
        self.history = []  # 记录每次交易后的持仓变化

    def __str__(self):
        """返回当前持仓状态的字符串表示"""
        return (f"股票 [{self.stock_code}-{self.stock_name}] 持仓状态："
                f"\n  当前数量：{self.current_shares:.2f}股"
                f"\n  持仓金额：{self.total_investment:.2f}元"
                f"\n  持仓成本：{self.average_cost:.5f}元/股"
                f"\n  累计收益：{self.realized_profit:.2f}元")

    #处理交易数据
    def process_trades(self):
        # 筛选当前股票的数据并按日期排序
        stock_trades = self.trade_data.sort_values('trade_date')

        # 处理每一条交易记录
        for _, trade in stock_trades.iterrows():
            trade_type = "买入" if trade['isbuy'] else "卖出"

            # 打印交易详情
            print(f"处理 {trade['trade_date']} {trade_type}: "
                  f"{trade['trade_number']}股 @ {trade['trade_price']}元")

            # 更新持仓状态
            if trade['isbuy']:  # 买入操作
                self._handle_buy(trade['trade_number'], trade['trade_price'])
            else:  # 卖出操作
                self._handle_sell(trade['trade_number'], trade['trade_price'])

            # 记录交易后状态
            self._record_state(trade['trade_date'])

    def _handle_buy(self, quantity: float, price: float):
        """处理买入交易逻辑"""
        self.current_shares += quantity
        self.total_investment += quantity * price

        # 计算新的持仓成本（避免除零错误）
        if self.current_shares == 0:
            self.average_cost = 0.0
        else:
            self.average_cost = round(self.total_investment / self.current_shares, 5)

    def _handle_sell(self, quantity: float, price: float):
        # 检查卖出数量是否超过当前持仓
        if quantity > self.current_shares:
            actual_sell = self.current_shares
            print(f"警告: 卖出数量({quantity}) > 当前持仓({self.current_shares})，已调整为卖出{actual_sell}股")
        else:
            actual_sell = quantity

        # 卖出成本 = 本次卖出数量 * 当前平均成本
        sold_cost = actual_sell * self.average_cost
        # 卖出所得现金 = 卖出数量 * 卖出价格
        sale_value = actual_sell * price

        # 准确计算本次交易的收益
        trade_profit = sale_value - sold_cost

        # 更新账户状态
        self.realized_profit += trade_profit
        self.current_shares -= actual_sell

        # 按成本减少总金额
        self.total_investment -= sold_cost

        # 重新计算平均成本（避免除零错误）
        if self.current_shares == 0:
            self.average_cost = 0.0
        else:
            self.average_cost = round(self.total_investment / self.current_shares, 5)

    def _record_state(self, date: str):
        """记录当前持仓状态到历史"""
        self.history.append({
            'date': date,
            'shares': self.current_shares,
            'total_investment': self.total_investment,
            'average_cost': self.average_cost,
            'realized_profit': self.realized_profit
        })

    def get_history(self) -> pd.DataFrame:
        """获取持仓变化历史"""
        return pd.DataFrame(self.history)