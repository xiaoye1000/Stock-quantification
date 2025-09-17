#获取阳包阴的技术形态/阴包阳的技术形态

#处理阳包阴数据
def get_bullish_cover_bearish(code_name_map,kline_10days_data,now_price , open_prices):
    filtered_data = {}
    filtered_now_price = {}
    filtered_open_prices = {}

    #先筛选
    for code in code_name_map.keys():
        if code in kline_10days_data:
            filtered_data[code] = kline_10days_data[code]

        if code in now_price:
            filtered_now_price[code] = now_price[code]

        if code in open_prices:
            filtered_open_prices[code] = open_prices[code]

    #print(filtered_data)
    #print(filtered_now_price)
    #print(filtered_open_prices)

    result = {}
    max_search_days = 5
    for code, kline_data in filtered_data.items():
        # 检查是否有必要的数据
        if code not in filtered_now_price or code not in filtered_open_prices:
            continue

        # 获取当前价格和开盘价
        current_price = filtered_now_price[code]
        open_price = filtered_open_prices[code]

        # 开盘价空值处理
        if open_price is None:
            open_price = current_price

        # 检查是否为阳线（当前价大于开盘价）
        if current_price <= open_price:
            continue

        # 在历史数据中寻找阴线（从后往前搜索）
        found_bearish = False
        bearish_high = 0

        # 从最近一天开始向前搜索（最多max_search_days天）
        for i in range(min(max_search_days, len(kline_data))):
            # 获取历史数据（索引-1表示最近一天，-2表示前一天，依此类推）
            day_data = kline_data[-1 - i]
            status = day_data[2]  # 涨跌状态

            # 找到阴线
            if status == -1:
                found_bearish = True
                bearish_high = day_data[0]  # 阴线的最高价
                break

        # 如果找到阴线且当前价高于阴线最高价
        if found_bearish and current_price > bearish_high:
            result[code] = code_name_map[code]

    return result