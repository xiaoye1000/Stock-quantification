from ..src.SQLbase.SQLite_manage import query_one_stock_table


def get_float_market_cap(stock_code: str) -> float:
    """
    计算单个股票的流通市值（上一个交易日）

    参数:
        stock_code: 带前缀的股票代码 (如'sz.000001')

    返回:
        流通市值（单位：元），如果无法计算则返回None
    """
    table_name = "STOCK000001"

    # 获取股票数据
    stock_data = query_one_stock_table(table_name, stock_code)

    # 过滤停牌数据
    stock_data = stock_data[stock_data['tradestatus'] == 1]

    # 检查是否有有效数据
    if stock_data.empty:
        return None

    # 获取最后一个交易日的数据
    last_row = stock_data.iloc[-1]

    # 获取必要字段
    volume = last_row['volume']  # 成交量（股）
    turn = last_row['turn']  # 换手率（百分比）
    close = last_row['close']  # 收盘价（元）

    # 检查换手率是否为0（避免除零错误）
    if turn == 0:
        return None

    # 计算流通股数量：成交量 / (换手率/100)
    float_shares = volume / (turn / 100)

    # 计算流通市值：流通股数量 × 收盘价
    float_market_cap = float_shares * close

    return float_market_cap


def filter_by_market_cap(code_name_map: dict) -> dict:
    """
    筛选流通市值小于500亿的股票

    参数:
        code_name_map: 股票代码-名称映射字典

    返回:
        筛选后的股票代码-名称映射字典
    """
    filtered_map = {}

    for stock_code, stock_name in code_name_map.items():
        # 获取流通市值
        market_cap = get_float_market_cap(stock_code)

        # 检查市值是否有效且小于500亿
        if market_cap is not None and market_cap < 5e10:  # 500亿 = 5e10
            filtered_map[stock_code] = stock_name

    return filtered_map