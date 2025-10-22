#判断利润回撤/止损

def profit_pulled_back(code_name_map,kline_10days_data,now_price):
    # 初始化结果字典
    result = {}

    # 遍历所有股票代码
    for code in code_name_map.keys():
        # 检查必要数据是否存在
        if code not in kline_10days_data or code not in now_price:
            continue

        # 获取该股票的K线数据和当前价格
        kline_data = kline_10days_data[code]
        current_price = now_price[code]

        # 确保有足够的数据（至少1天）
        if len(kline_data) == 0:
            continue

        # 获取近3日数据（最多取最后3个交易日）
        recent_days = min(3, len(kline_data))
        last_3_days = kline_data[-recent_days:]

        # 计算近3日最高收盘价
        max_high = max(day_data[4] for day_data in last_3_days)

        pulled_back = 0.1

        # 计算回撤比例（避免除零错误）
        if max_high > 0:
            pullback_ratio = (max_high - current_price) / max_high
            # 检查是否回撤超过5%
            if pullback_ratio >= pulled_back:
                result[code] = code_name_map[code]

    return result