#获取各种均线

"""
以五日均线为例，先获取前四日的收盘价,
再根据实时数据计算五日均线

二十日、六十日均线等同理
"""


def calculate_sma(prices, ma_period=5):
    """
    计算股票的移动平均线价格
    stock_60days_data: 字典，键为股票代码，值为60个价格列表（最新价格在最后）
    ma_period: 均线周期，整数，范围在3到60之间（默认5）
    """
    # 验证均线周期参数
    if not 3 <= ma_period <= 60:
        raise ValueError("均线周期必须在3到60之间")

    # 确保有足够的数据计算均线
    if len(prices) < ma_period:
        # 如果数据不足，使用所有可用数据计算
        period = len(prices)
        ma_value = sum(prices) / period
    else:
        # 取最后ma_period个价格计算均线
        recent_prices = prices[-ma_period:]
        ma_value = sum(recent_prices) / ma_period

    return ma_value
