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

条件1：
    均线多头排列，5均在10均之上，10均在20均之上，等等
条件2：
    当前股价在5均之上
条件3：
    股价出现阳包阴，缓冲30分钟
    即当前股价出现阳线，当前价格超过了上一根阴线的高点

条件5：
    各类技术指标加分

买入仓位策略：
    加权条件1：
        股价在前a日处于横盘窄幅震荡，波动率不超过b，监控这几日的最高点，
        阳包阴没有超过近日高点减分，超过加分

-----------------------------------------------------------------
卖出/减仓/止损条件：
条件1：
    股价出现阴包阳并且跌破五日均线
条件2：
    股价在距离近日最高点回撤超过x
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
#日期
from datetime import datetime, timedelta

#获取股票池
from ..src.SQLbase.SQLite_manage import (
    load_stock_mapping
)

#获取股票基本数据
from ..src.data_acquisition.stock_get import bs_query_ipodate

#获取均线
from ..technocal_indicators.get_sma import (
    calculate_sma
)
from ..technocal_indicators.get_data_for_indicators import get_59days_data

#获取实时数据（pytdx）
from ..src.data_acquisition.stock_get_tdx import pytdx_nowdata_stock

#阳包阴/阴包阳技术获取
from ..technocal_indicators.get_bullish_bearish import (
    get_bullish_cover_bearish
)

#股票池
from ..technocal_indicators.connect_monitoring_pool import connect_monitoring_pool

class StockFilter:
    """
    股票筛选器类，用于存储股票表数据
    """
    def __init__(self):
        """
        初始化股票筛选器
        """
        # 存储股票表数据
        self.code_name_map = None  # 初始化为None，稍后可以赋值

#获取全名称代码，在初筛使用
def get_all_stock_code():
    code_name_map = load_stock_mapping()
    return code_name_map

#获取上市日期
def get_recent_ipo_stocks(stock_basic_df, months=4):
    """
    预处理并对比所有上市日期与当前日期，返回上市时间在指定月数以内的股票代码列表
    """
    # 获取当前日期
    current_date = datetime.now()
    # 计算阈值日期
    threshold_date = current_date - timedelta(days = 30*months)  # 简单按30天每月计算

    recent_ipo_stocks = []

    # 创建一个股票代码到上市日期的映射字典
    for _, row in stock_basic_df.iterrows():
        code = row['code']
        ipo_date_str = row['ipoDate']

        try:
            # 将字符串转换为datetime对象
            ipo_date = datetime.strptime(ipo_date_str, "%Y-%m-%d")

            # 判断是否在指定月数内
            if ipo_date > threshold_date:
                recent_ipo_stocks.append(code)
        except (ValueError, TypeError):
            # 日期格式错误或为空，跳过
            continue

    # 查找指定股票的上市日期
    return recent_ipo_stocks

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
        "exclude_new_stock": True  # 剔除新股
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

    stock_59days_close_data , kline_10days_data = get_59days_data(code_name_map)
    stock_require_data = {
        'close_data': stock_59days_close_data,  # 59天收盘价数据
        'kline_data': kline_10days_data  # 10天K线数据
    }
    return code_name_map, stock_require_data


#获取当前实时价格，再处理
def get_now_price(code_name_map):
    data = pytdx_nowdata_stock()
    now_price = {}
    open_prices = {}
    for index, row in data.iterrows():
        # 确定市场前缀
        market_prefix = 'sh.' if row['market'] == 1 else 'sz.'
        # 构造完整股票代码（确保6位数字格式）
        full_code = market_prefix + str(row['code']).zfill(6)

        # 只处理在code_name_map中存在的股票代码
        if full_code in code_name_map:
            now_price[full_code] = row['price']
            open_prices[full_code] = row['open']

    return now_price,open_prices

def get_60days_close_data(stock_59days_close_data,now_price):
    result = {}

    # 遍历所有股票代码
    for stock_code in stock_59days_close_data:
        # 检查该股票是否有实时价格
        if stock_code in now_price:
            # 获取59个历史收盘价
            historical_prices = stock_59days_close_data[stock_code]
            # 获取实时价格
            current_price = now_price[stock_code]
            # 组合成60个价格的列表
            combined_prices = historical_prices + [current_price]
            # 添加到结果字典
            result[stock_code] = combined_prices

    return result


# 二筛，实时判断
def apply_stock_filters_second(code_name_map,stock_require_data):
    filter_conditions = {
        "sma_bullish_alignment": True,  # 均线多头排列
        "price_greater_sma": True, #当前股价高于5均
        "bullish_cover_bearish": True #当前股价出现阳包阴
    }

    stock_59days_close_data = stock_require_data['close_data']
    kline_10days_data = stock_require_data['kline_data']

    now_price , open_prices = get_now_price(code_name_map)
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

    return code_name_map

#处理股票为股票池
def add_to_monitoring_pool(code_name_map):
    now_price, open_prices = get_now_price(code_name_map)
    connect_monitoring_pool(code_name_map, now_price)
    return 0