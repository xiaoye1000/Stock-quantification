#获取各种数据，用于该技术区域的数据获取

from ..src.SQLbase.SQLite_manage import query_one_stock_table

import pandas as pd

#首先获取59个交易日的股票数据
#用于策略集的函数
def get_59days_data(code_name_map):
    table_name = "STOCK000001"
    result_dict_close = {}
    result_dict_kline = {}

    for stock_code, stock_name in code_name_map.items():
        stock_data: pd.DataFrame = query_one_stock_table(table_name, stock_code)

        stock_data = stock_data[stock_data['tradestatus'] == 1]
        #----------------------------------------------------
        # 获取1：获取最后59个交易日的收盘价数据
        close_prices = stock_data['close'].tail(59).tolist()

        # 将股票代码和收盘价列表组合成键值对
        result_dict_close[stock_code] = close_prices

        #----------------------------------------------------
        # 获取2：获取最后10个交易日的最高价、最低价和K线状态
        last_10_data = stock_data.tail(10)
        kline_status_list = []

        for i in range(len(last_10_data)):
            current_day = last_10_data.iloc[i]

            # 处理可能的空值情况
            pct_chg_str = current_day['pctChg']

            # 如果pctChg是空字符串，视为平盘（0%）
            if pct_chg_str == '':
                pct_chg = 0.0
            else:
                try:
                    pct_chg = float(pct_chg_str)
                except ValueError:
                    # 如果转换失败，也视为平盘
                    pct_chg = 0.0

            if pct_chg > 0:
                status = 1  # 阳线
            elif pct_chg < 0:
                status = -1  # 阴线
            else:
                status = 0  # 平线

            kline_status_list.append([
                current_day['high'],
                current_day['low'],
                status
            ])

        result_dict_kline[stock_code] = kline_status_list

    return result_dict_close , result_dict_kline