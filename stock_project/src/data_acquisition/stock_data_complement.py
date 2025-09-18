#盘后下载数据、补充确实的数据

#交易日判断
from chinese_calendar import is_workday

#日期
from datetime import datetime, timedelta

#引用数据库
from ..SQLbase.SQLite_manage import (
    query_one_stock_table,
    stock_to_sql_for
)

# 判断所给日期是否为交易日
def is_trade_day(date):
    if is_workday(date):
        if datetime.isoweekday(date) < 6:
            return True
    return False

#获取日期，返回数据库空缺的交易时间段
def date_get():
    try:
        table_name = 'STOCK000001'
        data = query_one_stock_table(table_name, stock_code='sh.600000')

        # 检查是否成功获取数据
        if data is None or data.empty:
            print('数库据数据为空，或无法查询')
            return None, None

        last_date_str = data['date'].iloc[-1]  # 直接取最后一行日期

        # 将字符串转换为 datetime 对象
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")

        # 加一天
        next_date = last_date + timedelta(days=1)

        # 获取当前天
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()

        # 判断日期：下一天应该不晚于当前日期
        if next_date.date() > current_date:
            return None, None  # 返回空值

        # 检查时间段内是否有交易日
        has_trade_day = False
        temp_date = next_date
        while temp_date.date() <= current_date:
            if is_trade_day(temp_date.date()):
                has_trade_day = True
                break
            temp_date += timedelta(days=1)

        if not has_trade_day:
            print("区间内无交易日，无需补充数据")
            return None, None

        # 检查是否在有效补充时段（交易日后16:00至次日开盘前）
        if next_date.date() == current_date:
            # 检查当前时间是否在下午4点之后
            if current_time.hour < 16:
                print(f"当前时间未到下午4点({current_time.strftime('%H:%M')})，请在16:00后补充当日数据")
                return None, None  # 未到补充时段返回空值

        return next_date.strftime("%Y-%m-%d"), current_datetime.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"获取日期出错: {str(e)}")
        return None, None  # 任何异常返回空值

#补充数据
def data_complement():
    start_date, end_date = date_get()
    # 当获取不到有效日期时直接返回空值
    if start_date is None or end_date is None:
        return None

    table_name = 'STOCK000001'

    try:
        stock_to_sql_for(table_name,start_date, end_date)
        print(f"补充数据从 {start_date} 到 {end_date}")
        return "数据补充成功"

    except Exception as e:
        print(f"补充数据出错: {str(e)}")
        return 0