#获取各种数据，用于该技术区域的数据获取

from ..src.SQLbase.SQLite_manage import query_one_stock_table

import pandas as pd

from datetime import datetime


# 判断当前是否处于收盘后时间（周一到周五16点后到次日6点前，或周末全天）
def is_after_close():
    now = datetime.now()
    weekday = now.weekday()  # 周一0 → 周日6
    hour = now.hour

    # 周末全天视为收盘后
    if weekday >= 5:  # 周六(5)或周日(6)
        return True

    # 工作日：16点后到次日6点前
    if hour >= 16 or hour < 6:
        return True

    return False

#首先获取59个交易日的股票数据
#用于策略集的函数
def get_59days_data(code_name_map):
    table_name = "STOCK000001"
    result_dict_close = {}
    result_dict_kline = {}

    # 判断是否收盘后
    after_close = is_after_close()

    for stock_code, stock_name in code_name_map.items():

        stock_data: pd.DataFrame = query_one_stock_table(table_name, stock_code)
        stock_data = stock_data[stock_data['tradestatus'] == 1]

        #----------------------------------------------------
        # 获取1：获取最后59个交易日的收盘价数据
        if after_close:
            # 收盘后：取倒数第2个到倒数第60个（共59条）
            close_prices = stock_data['close'].iloc[-60:-1].tolist()
        else:
            # 交易时间：正常取最后59条
            close_prices = stock_data['close'].tail(59).tolist()

        # 将股票代码和收盘价列表组合成键值对
        result_dict_close[stock_code] = close_prices

        #----------------------------------------------------
        # 获取2：获取最后10个交易日的最高价、最低价和K线状态
        if after_close:
            # 收盘后：取倒数第2个到倒数第11个（共10条）
            last_10_data = stock_data.iloc[-11:-1]
        else:
            # 交易时间：正常取最后10条
            last_10_data = stock_data.tail(10)

        kline_status_list = []

        for i in range(len(last_10_data)):
            current_day = last_10_data.iloc[i]

            # 使用开盘价和收盘价判断K线状态
            open_price = current_day['open']
            close_price = current_day['close']

            if close_price > open_price:
                status = 1  # 阳线（收盘价高于开盘价）
            elif close_price < open_price:
                status = -1  # 阴线（收盘价低于开盘价）
            else:
                status = 0  # 平线（收盘价等于开盘价）

            kline_status_list.append([
                current_day['high'],
                current_day['low'],
                status
            ])

        result_dict_kline[stock_code] = kline_status_list

    return result_dict_close , result_dict_kline