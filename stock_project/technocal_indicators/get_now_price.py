#获取当前实时价格，再处理

#获取实时数据（pytdx）
from ..src.data_acquisition.stock_get_tdx import pytdx_nowdata_stock

def get_now_price(code_name_map,api):
    data = pytdx_nowdata_stock(api=api)
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