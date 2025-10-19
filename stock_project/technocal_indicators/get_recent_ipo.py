#获取上市日期
#日期
from datetime import datetime, timedelta

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