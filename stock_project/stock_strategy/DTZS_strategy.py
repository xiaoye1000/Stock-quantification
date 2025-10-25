#多头择时量化策略（股票）

"""
选股策略：
筛选1（初筛）：
    条件1：
        若权限不足，剔除创业板，科创板，新股
    条件2：
        剔除st股票
    条件3：
        剔除上市4个月内的新股
    条件4:
        市值条件筛选，剔除市值大于500亿的股票

条件1：
    均线多头排列，5均在10均之上，10均在20均之上，等等
条件2：
    当前股价在5均之上
条件3：
    股价出现阳包阴，缓冲30分钟
    即当前股价出现阳线，当前价格超过了上一根阴线的高点
条件4：
    剔除在一段区间内，股票震荡格局，即x日内最高最低涨跌幅不超过x，当前股价未超过前x日的某一天最高价

条件5：
    各类技术指标加分

买入仓位策略：

    分仓策略：
        1.设定开仓最高上限a，开仓最低分仓金额b。
            资金规模较小时，分仓数较少。资金规模较多时，限制最高开仓数，平均分配资金

    加权条件1：
        股价在前a日处于横盘窄幅震荡，波动率不超过b，监控这几日的最高点，
        阳包阴没有超过近日高点减分，超过加分


-----------------------------------------------------------------
卖出/减仓/止损条件：
条件1：
    股价出现阴包阳并且跌破五日均线
条件2：
    股价在距离近日最高收盘价回撤超过x
条件3：
    当日跌幅达到a以下，超过半个小时，或者当日跌幅达到b以下
条件4：
    各类技术指标减分

卖出仓位策略：
    加权条件1：
        当日/近日大盘指数影响分
    加权条件2：
        当日/近日该板块影响分
"""

#获取股票池
from ..src.SQLbase.SQLite_manage import (
    load_stock_mapping
)

#获取股票基本数据
from ..src.data_acquisition.stock_get import bs_query_ipodate

#获取上市日期
from ..technocal_indicators.get_recent_ipo import get_recent_ipo_stocks

#获取均线
from ..technocal_indicators.get_sma import (
    calculate_sma
)

#获取59日数据，整合当前实时数据为60日数据
from ..technocal_indicators.get_data_for_indicators import (
    get_59days_data,
    get_60days_close_data
)

#获取当前实时价格
from ..technocal_indicators.get_now_price import get_now_price

#阳包阴/阴包阳技术获取
from ..technocal_indicators.get_bullish_bearish import (
    get_bullish_cover_bearish,
    get_bearish_cover_bullish
)

#回撤函数
from ..technocal_indicators.profit_pulled_back import profit_pulled_back

#股票池
from ..technocal_indicators.connect_monitoring_pool import (
    connect_monitoring_pool,
    remove_from_monitoring_pool
)

#市值计算
from ..technocal_indicators.get_stock_market_value import  filter_by_market_cap

#获取全名称代码，在初筛使用
def get_all_stock_code():
    code_name_map = load_stock_mapping()
    return code_name_map

#初筛，无需二次判断
def apply_stock_filters_first(code_name_map):
    """
    应用股票筛选条件
    :param code_name_map: 股票
    """
    # 初始化结果为通过筛选
    # 筛选条件
    filter_conditions = {
        "exclude_gem": True,  # 剔除创业板
        "exclude_star_market": True,  # 剔除科创板
        "exclude_st": True,  # 剔除ST股
        "exclude_new_stock": True,  # 剔除新股
        "exclude_market_value":True  #市值筛选
    }

    # 检查每个筛选条件
    #------------------------------------------------------------------
    #筛选创业板股票（代码以3开头）
    if filter_conditions.get("exclude_gem", True):
        # 创建待删除的键列表
        to_remove = []

        # 遍历字典
        for stock_code, stock_name in code_name_map.items():
            # 提取数字部分（去掉'sz.'或'sh.'前缀）
            if '.' in stock_code:
                code_num = stock_code.split('.')[1]

                # 判断是否为创业板（代码以3开头）
                if code_num.startswith('3'):
                    to_remove.append(stock_code)
            else:
                # 对于没有点号的代码，直接检查是否以3开头
                if stock_code.startswith('3'):
                    to_remove.append(stock_code)

        # 从原字典中删除创业板股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    #筛选科创，以68开头的股票
    if filter_conditions.get("exclude_star_market", True):
        # 创建待删除的键列表
        to_remove = []

        # 遍历字典，筛选科创板股票（代码以68开头）
        for stock_code, stock_name in code_name_map.items():
            # 提取数字部分（去掉'sz.'或'sh.'前缀）
            if '.' in stock_code:
                code_num = stock_code.split('.')[1]

                # 判断是否为科创板（代码以68开头）
                if code_num.startswith('68'):
                    to_remove.append(stock_code)
            else:
                # 对于没有点号的代码，直接检查是否以68开头
                if stock_code.startswith('68'):
                    to_remove.append(stock_code)

        # 从原字典中删除科创板股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    #剔除st股票
    if filter_conditions.get("exclude_st", True):
        # 创建待删除的键列表
        to_remove = []

        # 遍历字典，筛选ST股票（名称中包含"ST"）
        for stock_code, stock_name in code_name_map.items():
            if "ST" in stock_name:
                to_remove.append(stock_code)

        # 从原字典中删除ST股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    #剔除新股
    if filter_conditions.get("exclude_new_stock", True):
        # 创建待删除的键列表
        to_remove = []

        stock_basic_df = bs_query_ipodate()

        # 获取上市4个月以内的股票代码列表
        recent_ipo_stocks = get_recent_ipo_stocks(stock_basic_df, months=4)

        # 遍历股票代码映射，检查是否在新股列表中
        for stock_code, stock_name in code_name_map.items():
            if stock_code in recent_ipo_stocks:
                to_remove.append(stock_code)

        # 从原字典中删除新股
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    #剔除市值x亿以上的股票
    if filter_conditions.get("exclude_market_value", True):
        code_name_map = filter_by_market_cap(code_name_map)

    stock_59days_close_data , kline_10days_data = get_59days_data(code_name_map)
    stock_require_data_buy = {
        'close_data': stock_59days_close_data,  # 59天收盘价数据
        'kline_data': kline_10days_data  # 10天K线数据
    }
    return code_name_map, stock_require_data_buy

# 二筛，实时判断
def apply_stock_filters_second(code_name_map,stock_require_data_buy,api):
    filter_conditions = {
        "sma_bullish_alignment": True,  # 均线多头排列
        "price_greater_sma": True, #当前股价高于5均
        "bullish_cover_bearish": True, #当前股价出现阳包阴
        "remove_oscillation_stocks":True #剔除震荡格局
    }

    stock_59days_close_data = stock_require_data_buy['close_data']
    kline_10days_data = stock_require_data_buy['kline_data']

    now_price , open_prices = get_now_price(code_name_map,api)
    stock_60days_close_data = get_60days_close_data(stock_59days_close_data, now_price)

    # 创建字典来存储每只股票的均线值
    ma_results = {}

    # 遍历所有股票
    for stock_code, prices in stock_60days_close_data.items():
        # 计算5日、20日、60日均线
        ma5 = calculate_sma(prices, 5)
        ma10 = calculate_sma(prices, 10)
        ma20 = calculate_sma(prices, 20)
        ma60 = calculate_sma(prices, 60)

        # 存储计算结果
        ma_results[stock_code] = {
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'ma60': ma60,
            'current_price': prices[-1]  # 最后一个是当前价格
        }
    # ------------------------------------------------------------------
    #均线多头排列
    if filter_conditions.get("sma_bullish_alignment", True):
        # 创建待删除的键列表
        to_remove = []

        # 遍历所有股票，筛选均线多头排列
        for stock_code, ma_data in ma_results.items():
            # 检查均线多头排列条件：5日 > 10日 > 20日 > 60日
            if not (ma_data['ma5'] > ma_data['ma10'] >
                    ma_data['ma20'] > ma_data['ma60']):
                to_remove.append(stock_code)

        # 从原字典中删除不满足条件的股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    # 当前股价高于5均
    if filter_conditions.get("price_greater_sma", True):
        # 创建待删除的键列表
        to_remove = []

        # 遍历所有股票，筛选股价大于5均
        for stock_code, ma_data in ma_results.items():
            if not (ma_data['current_price'] > ma_data['ma5']):
                to_remove.append(stock_code)

        # 从原字典中删除不满足条件的股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    # 当前股价出现阳包阴
    if filter_conditions.get("bullish_cover_bearish", True):
        code_name_map = get_bullish_cover_bearish(code_name_map, kline_10days_data, now_price, open_prices)

    # ------------------------------------------------------------------
    # 剔除震荡格局的股票
    if filter_conditions.get("remove_oscillation_stocks", True):
        pass

    return code_name_map

#处理股票为股票池
def add_to_monitoring_pool(code_name_map,api):
    now_price, open_prices = get_now_price(code_name_map,api)
    connect_monitoring_pool(code_name_map, now_price)
    return None

#
def remove_stock_from_monitoring_pool(code_name_map,api):
    now_price, open_prices = get_now_price(code_name_map,api)
    remove_from_monitoring_pool(code_name_map, now_price)
    return None

#分仓策略
def stock_position_sizing(total_capital):
    """
    股票分仓策略函数
    :param total_capital: 总资金量（单位：元）
    :return: (开仓数量, 每只股票分配资金)
    """
    # 定义策略参数
    MIN_POSITION_SIZE = 10000  # 最小分仓金额1万元
    MAX_POSITIONS = 80  # 最大开仓数量

    # 如果资金不足最小分仓金额，无法开仓
    if total_capital < MIN_POSITION_SIZE:
        return 0, 0.0

    # 计算最大可能开仓数量（基于最小分仓金额）
    max_positions_by_capital = total_capital // MIN_POSITION_SIZE

    # 确定实际开仓数量（不超过上限）
    position_count = min(max_positions_by_capital, MAX_POSITIONS)

    # 确保至少开1个仓位
    position_count = max(int(position_count), 1)

    # 计算每只股票分配资金（保留两位小数）
    capital_per_stock = round(total_capital / position_count, 2)

    return position_count, capital_per_stock

#卖出条件筛选
#预处理数据
def apply_selling_stocks_first(code_name_map):
    stock_59days_close_data, kline_10days_data = get_59days_data(code_name_map)
    stock_require_data_sell = {
        'close_data': stock_59days_close_data,  # 59天收盘价数据
        'kline_data': kline_10days_data  # 10天K线数据
    }
    return code_name_map, stock_require_data_sell

#第二次，正式处理
def apply_selling_stocks_second(code_name_map,stock_require_data_sell,api):
    filter_conditions = {
        "price_lower_5sma_and_bearish_cover_bullish": True,  #股价跌破5日均线并且阴包阳
        "recent_high_retreated": True,  #股价在距离近日最高点回撤超过x%
        "price_lower_10sma": True, #股价跌破10日均线
    }

    stock_59days_close_data = stock_require_data_sell['close_data']
    kline_10days_data = stock_require_data_sell['kline_data']

    now_price, open_prices = get_now_price(code_name_map,api)
    stock_60days_close_data = get_60days_close_data(stock_59days_close_data, now_price)

    # 创建字典来存储每只股票的均线值
    ma_results = {}

    # 初始化卖出股票列表
    selling_stocks_dict = {}

    # 遍历所有股票
    for stock_code, prices in stock_60days_close_data.items():
        # 计算5日、20日、60日均线
        ma5 = calculate_sma(prices, 5)
        ma10 = calculate_sma(prices, 10)
        ma20 = calculate_sma(prices, 20)
        ma60 = calculate_sma(prices, 60)

        # 存储计算结果
        ma_results[stock_code] = {
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'ma60': ma60,
            'current_price': prices[-1]  # 最后一个是当前价格
        }

    # ------------------------------------------------------------------
    # 股价出现阴包阳并且跌破5日均线
    if filter_conditions.get("price_lower_5sma_and_bearish_cover_bullish", True):
        # 获取阴包阳的股票列表
        bearish_stocks = get_bearish_cover_bullish(code_name_map, kline_10days_data, now_price, open_prices)

        for stock_code, ma_data in ma_results.items():
            if stock_code not in selling_stocks_dict:
                if stock_code in bearish_stocks and ma_data['current_price'] < ma_data['ma5']:
                    # 直接添加到字典
                    selling_stocks_dict[stock_code] = code_name_map.get(stock_code, "未知股票")

    # ------------------------------------------------------------------
    #股价在距离近日最高收盘价回撤超过10%
    if filter_conditions.get("recent_high_retreated", True):
        pulled_back_stocks = profit_pulled_back(code_name_map,kline_10days_data,now_price)
        for stock_code, stock_name in pulled_back_stocks.items():
            # 只添加尚未存在的股票
            if stock_code not in selling_stocks_dict:
                selling_stocks_dict[stock_code] = stock_name

    # ------------------------------------------------------------------
    # 股价跌破10日均线
    if filter_conditions.get("price_lower_10sma", True):
        for stock_code, ma_data in ma_results.items():
            # 检查股价是否低于10日均线
            if ma_data['current_price'] < ma_data['ma10']:
                if stock_code not in selling_stocks_dict:
                    selling_stocks_dict[stock_code] = code_name_map.get(stock_code, "未知股票")

    return selling_stocks_dict