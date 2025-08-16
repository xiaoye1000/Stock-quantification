#数据库
from ..SQLbase.SQLite_manage import (
    query_trade_table
)

#可视化接口引用
from ..SQLbase.stock_matplotlib_interface import *

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
        self.current_shares = 0.0  # 当前持仓数量
        self.total_investment = 0.0  # 当前持仓总金额（买入总金额 - 卖出总金额）
        self.average_cost = 0.0  # 当前持仓成本（总金额/持仓数量）
        self.realized_profit = 0.0  # 累计实现收益（卖出收益）

        self.aligned_history = None

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
            #trade_type = "买入" if trade['isbuy'] else "卖出"

            # 打印交易详情
            #print(f"处理 {trade['trade_date']} {trade_type}: "
            #      f"{trade['trade_number']}股 @ {trade['trade_price']}元")

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

    def get_stock_code(self) -> str:
        """返回当前持仓的股票代码"""
        return self.stock_code

    def get_full_history(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """获取扩展到整个交易日期间的完整持仓历史"""
        # 检查是否为空
        if len(self.history) == 0:
            raise RuntimeError("先调用process_trades()计算交易历史")

        # 处理股票数据中的重复日期 - 保留每个日期的最后一条记录
        stock_data = stock_data[~stock_data.index.duplicated(keep='last')]

        # 只保留交易日期之后的数据
        start_date = self.history[0]['date']
        filtered_stock = stock_data[stock_data.index >= start_date].copy()

        # 创建完整的时间序列框架
        full_history = pd.DataFrame(index=filtered_stock.index)
        # 使用固定列名初始化
        cols = ['shares', 'total_investment', 'average_cost', 'realized_profit']
        for col in cols:
            full_history[col] = np.nan

        # 将历史交易记录转为DataFrame并设置日期索引
        history_df = pd.DataFrame(self.history)
        history_df['date'] = pd.to_datetime(history_df['date'])
        history_df = history_df.set_index('date')

        # 遍历每个交易日，填充状态
        for date, row in history_df.iterrows():
            # 只处理在股票数据索引中存在的日期
            if date in full_history.index:
                for col in cols:
                    full_history.loc[date, col] = row[col]

        # 前向填充（持仓状态保持不变）
        full_history[cols] = full_history[cols].ffill()

        # 在首次交易前，持仓和收益均为0
        full_history[cols] = full_history[cols].fillna(0)

        return full_history

#获取类中的历史交易函数
def get_trade_data(trade_table):
    tradecode = StockPosition(trade_table)
    tradecode.process_trades()
    return tradecode.get_history() , tradecode.get_stock_code()

# 获取填充过的完整时间轴的历史数据的函数
def get_full_trade_history(trade_table, stock_data):
    tradecode = StockPosition(trade_table)
    tradecode.process_trades()
    full_history = tradecode.get_full_history(stock_data=stock_data)
    return full_history, tradecode.get_stock_code()

#交易数据整理，为输入数据做准备
#内置函数，无需使用
def extract_signals(trade_table):
    trade_data = query_trade_table(trade_table)
    # 筛选有效交易信号
    signals = trade_data[['trade_date', 'isbuy', 'trade_price']].copy()

    # 添加交易类型列
    signals['type'] = signals['isbuy'].map({1: 'buy', 0: 'sell'})

    return signals

#-------------------------------------------------------------------------
#连接到可视化接口函数
#交易过程可视化
class TradePlot(MplTypesDraw):
    # 实例化DefTypesPool
    app = DefTypesPool()
    #-------------------------------------
    #k线图
    @app.route_types("ochl")
    def ochl_graph(self, sub_graph, stock_dat, df_dat=None):
        # K线数据
        type_dict = {'open': stock_dat.open,
                     'close': stock_dat.close,
                     'high': stock_dat.high,
                     'low': stock_dat.low
                     }
        view_function = MplTypesDraw.mpl.route_output("ochl")
        view_function(stock_dat.index, type_dict, sub_graph)

    # -------------------------------------
    # 买卖点标注
    @app.route_types("trade_points")
    def trade_points(self, sub_graph, stock_dat, signals=None):
        if signals is None:
            return

        # 创建买卖点位置列表
        buy_dates, buy_prices, sell_dates, sell_prices = [], [], [], []

        for _, row in signals.iterrows():
            # 找到对应日期在数据中的位置
            if row['trade_date'] in stock_dat.index:
                idx = stock_dat.index.get_loc(row['trade_date'])

                if row['type'] == 'buy':
                    buy_dates.append(idx)
                    buy_prices.append(row['trade_price'])
                elif row['type'] == 'sell':
                    sell_dates.append(idx)
                    sell_prices.append(row['trade_price'])

        # 绘制买点(红色)
        if buy_dates:
            sub_graph.scatter(buy_dates, buy_prices, color='red', s=40, zorder=10,
                              edgecolors='black', label='买入')

        # 绘制卖点(绿色)
        if sell_dates:
            sub_graph.scatter(sell_dates, sell_prices, color='green', s=40, zorder=10,
                              edgecolors='black', label='卖出')

    # -------------------------------------
    # 交易信号标记
    @app.route_types("trade_signals")
    def trade_signals_marker(self, sub_graph, stock_dat, signals=None):
        if signals is None:
            return

        # 获取最高价用于定位标记
        max_price = stock_dat['high'].max()
        offset = max_price * 0.05  # 标记位置偏移量
        mark_height = max_price * 1.05  # 标记文字位置的高度

        for date in signals['trade_date'].unique():
            # 找到对应日期在数据中的位置
            if date in stock_dat.index:
                idx = stock_dat.index.get_loc(date)

                # 获取当日最高价作为虚线起点
                day_high = stock_dat.loc[date, 'high'] if date in stock_dat.index else stock_dat['high'].max()

                # 获取该日期所有交易类型
                date_signals = signals[signals['trade_date'] == date]
                signal_types = set(date_signals['type'])

                # 确定信号标记文字
                if 'buy' in signal_types and 'sell' in signal_types:
                    text = 'T'
                    color = 'purple'
                elif 'buy' in signal_types:
                    text = 'B'
                    color = 'red'
                elif 'sell' in signal_types:
                    text = 'S'
                    color = 'green'
                else:
                    continue

                # 绘制虚线：从当日K线最高价到标记文字位置
                sub_graph.plot([idx, idx], [day_high, mark_height],
                                   color='grey', linestyle='--', alpha=0.7)

                # 添加信号标记
                sub_graph.annotate(
                    text,
                    xy=(idx, max_price + offset),
                    xycoords='data',
                    ha='center',
                    va='center',
                    fontsize=10,
                    fontweight='bold',
                    bbox=dict(boxstyle='square', facecolor=color, edgecolor='black', alpha=0.8)
                )

    # -------------------------------------
    # 收益曲线
    @app.route_types("profit_curve")
    def profit_curve(self, sub_graph, profit_data):
        """绘制收益曲线"""
        print(f"收益曲线数据量: {len(profit_data)}条")  # 调试输出

        # 确保数据有效
        if profit_data.empty:
            print("警告: 收益数据为空")
            return

        # 确保有realized_profit列
        if 'realized_profit' not in profit_data.columns:
            print("警告: 收益数据中缺少realized_profit列")
            print(f"可用列: {profit_data.columns.tolist()}")
            return

        # 获取位置索引（整数值）
        positions = range(len(profit_data))
        profits = profit_data['realized_profit'].values

        print(f"收益数据示例: {profits[:5]}")  # 调试输出

        # 绘制收益曲线
        sub_graph.plot(positions, profits, 'b-', linewidth=2, label='累计收益')
        sub_graph.fill_between(positions, profits, 0, where=(profits >= 0),
                               facecolor='green', alpha=0.3, interpolate=True)
        sub_graph.fill_between(positions, profits, 0, where=(profits < 0),
                               facecolor='red', alpha=0.3, interpolate=True)

        # 添加0水平线
        sub_graph.axhline(y=0, color='grey', linestyle='--')

        # 添加网格
        sub_graph.grid(True, linestyle='--', alpha=0.5)

    #构造函数
    def __init__(self, **kwargs):
        MplTypesDraw.__init__(self)
        # 图表参数
        self.graph_curr = None
        # 数据
        self.df_ohlc = None
        #交易数据
        self.trade = None
        # 创建fig对象
        self.fig = plt.figure(figsize=kwargs['figsize'], dpi=100, facecolor="white")

        self.graph_dict = {}

        try:
            gs = gridspec.GridSpec(kwargs['nrows'], kwargs['ncols'],
                                   left=kwargs['left'], bottom=kwargs['bottom'], right=kwargs['right'],
                                   top=kwargs['top'],
                                   wspace=kwargs['wspace'], hspace=kwargs['hspace'],
                                   height_ratios=kwargs['height_ratios'])
        except:
            raise Exception("para error")
        else:
            for i in range(0, kwargs['nrows'], 1):
                self.graph_dict[kwargs['subplots'][i]] = self.fig.add_subplot(gs[i, :])

    #子函数，用于绘制图表
    def graph_attr(self, **kwargs):

        if 'title' in kwargs.keys():
            self.graph_curr.set_title(kwargs['title'])

        if 'legend' in kwargs.keys():
            self.graph_curr.legend(loc=kwargs['legend'], shadow=True)

        if 'xlabel' in kwargs.keys():
            self.graph_curr.set_xlabel(kwargs['xlabel'])

        self.graph_curr.set_ylabel(kwargs['ylabel'])
        self.graph_curr.set_xlim(0, len(self.df_ohlc.index))  # 设置一下x轴的范围
        self.graph_curr.set_xticks(range(0, len(self.df_ohlc.index), kwargs['xticks']))  # X轴刻度设定 每15天标一个日期

        if 'xticklabels' in kwargs.keys():
            self.graph_curr.set_xticklabels(
                [self.df_ohlc.index.strftime(kwargs['xticklabels'])[index] for index in
                 self.graph_curr.get_xticks()])  # 标签设置为日期

            # X-轴每个ticker标签都向右倾斜45度
            for label in self.graph_curr.xaxis.get_ticklabels():
                label.set_rotation(45)
                label.set_fontsize(10)  # 设置标签字体
        else:
            for label in self.graph_curr.xaxis.get_ticklabels():
                label.set_visible(False)

    # 绘制子图
    def graph_run(self, stock_data,trade_history, **kwargs):
        self.df_ohlc = stock_data
        self.trade = trade_history
        for key in kwargs:
            self.graph_curr = self.graph_dict[kwargs[key]['graph_name']]
            for path, val in kwargs[key]['graph_type'].items():
                print("输出[%s]可视化图表:" % path)

                view_function = TradePlot.app.route_output(path)
                # 根据函数名调整参数传递
                if path == "profit_curve":
                    # 收益曲线只需要图表和收益数据
                    view_function(self , self.graph_curr, self.trade)
                else:
                    # 其他图表需要完整参数
                    view_function(self, self.graph_curr, self.df_ohlc, val)
            self.graph_attr(**kwargs[key])
        plt.show()


#-------------------------------------------
#主要绘图函数
def draw_integrated_interface(table_name, trade_table,start=None, end=None):

    trade_signals = extract_signals(trade_table)
    print(f"交易信号量: {len(trade_signals)}条")

    trade_history, stock_code = get_trade_data(trade_table)
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code, start, end)
    print(f"股票数据量: {len(stock_dat)}条")
    stock_dat.index = pd.to_datetime(stock_dat.index)

    # 创建持仓管理对象
    tradecode = StockPosition(trade_table)
    tradecode.process_trades()

    # 获取对齐后的完整持仓历史
    full_trade_history = tradecode.get_full_history(stock_dat)

    # 调试输出持仓数据
    print(f"持仓历史数据量: {len(full_trade_history)}条")

    # 4. 确保索引对齐
    if not stock_dat.index.equals(full_trade_history.index):
        print("警告: 股票数据和持仓历史索引不一致, 正在对齐...")
        common_index = stock_dat.index.intersection(full_trade_history.index)
        stock_dat = stock_dat.loc[common_index]
        full_trade_history = full_trade_history.loc[common_index]
        print(f"对齐后股票数据量: {len(stock_dat)}条")
        print(f"对齐后持仓历史量: {len(full_trade_history)}条")

    layout_dict = {'figsize': (12, 8),
                   'nrows': 2,
                   'ncols': 1,
                   'left': 0.07,
                   'bottom': 0.15,
                   'right': 0.99,
                   'top': 0.96,
                   'wspace': None,
                   'hspace': 0,
                   'height_ratios': [3,1],
                   'subplots': ['kgraph', 'profitgraph']}

    subplots_dict = {'graph_fst': {'graph_name': 'kgraph',
                                   'graph_type': {'ochl': None,
                                                  'trade_points': trade_signals,
                                                  'trade_signals': trade_signals
                                                  },
                                   'title': f"{full_name}-日K线",
                                   'ylabel': "价格",
                                   'xticks': 15,
                                   'legend': 'best'
                                   },
                     'graph_sec': {'graph_name': 'profitgraph',
                                   'graph_type': {'profit_curve': None
                                                  },
                                   'ylabel': "累计收益",
                                   'xlabel': "日期",
                                   'xticks': 15,
                                   'legend': 'best',
                                   'xticklabels': '%Y-%m-%d'
                                   },
                     }

    draw_stock = TradePlot(**layout_dict)
    draw_stock.graph_run(stock_data=stock_dat, trade_history=full_trade_history,**subplots_dict)
