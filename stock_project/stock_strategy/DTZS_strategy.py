#多头择时量化策略（股票）

"""
选股策略：
条件1：
    剔除st股票
条件1：
    均线多头排列，5均在10均之上，10均在20均之上，等等
条件2：
    当前股价在5均之上
条件3：
    股价出现阳包阴，缓冲30分钟
    即当前股价出现阳线，当前价格超过了上一根阴线的高点
条件4：
    （可选择条件）权限不足，剔除创业板，科创板，新股
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

#获取股票池
from ..src.SQLbase.SQLite_manage import (
    load_stock_mapping,
    query_one_stock_table
)



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

#获取全名称代码
def get_all_stock_code():
    code_name_map = load_stock_mapping()
    return code_name_map

def apply_stock_filters(code_name_map):
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
            # 判断是否为ST股票（名称中包含"ST"）
            if "ST" in stock_name:
                to_remove.append(stock_code)

        # 从原字典中删除ST股票
        for stock_code in to_remove:
            if stock_code in code_name_map:
                del code_name_map[stock_code]

    # ------------------------------------------------------------------
    if filter_conditions.get("exclude_new_stock", True):
        for stock_code, stock_name in code_name_map.items():
            table_name = 'STOCK000001'
            code_data = query_one_stock_table(table_name,stock_code)
            last_date_str = code_data['date'].iloc[0]

    return code_name_map