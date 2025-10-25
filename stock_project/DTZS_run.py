#运行函数

import time
from datetime import datetime

#多头择时策略
from .stock_strategy.DTZS_strategy import *

from .src.data_acquisition.get_stock_pool import *

#补充数据
from .src.data_acquisition.stock_data_complement import data_complement

#连接股票池
from .technocal_indicators.connect_monitoring_pool import get_monitoring_pool

#获取api
from stock_project.src.data_acquisition.stock_get_tdx import connect_tdx,api_disconnect


def dtzs_run(stop_event):
    #更新股票池
    get_all_stock_to_pool()

    #自动补全数据
    data_complement()

    #连接api
    api = connect_tdx()

    #一筛，预处理
    #买入数据处理
    print("执行买入预处理")
    code_name_map, stock_require_data = apply_stock_filters_first(get_all_stock_code())
    print("买入预处理完成")
    #卖出数据处理
    print("执行卖出预处理")
    code_name_map2, stock_require_data_sell = apply_selling_stocks_first(get_monitoring_pool())
    print("卖出预处理完成")
    test_i = 0

    # 无限循环部分（可随时停止）
    while not stop_event.is_set():
        try:
            # 获取当前时间
            current_time = datetime.now().time()
            skip_period_start = datetime.strptime("08:00:00", "%H:%M:%S").time()
            skip_period_end = datetime.strptime("09:30:00", "%H:%M:%S").time()

            # 检查是否在跳过时间段
            if skip_period_start <= current_time <= skip_period_end:
                print(f"当前时间 {current_time.strftime('%H:%M:%S')} 在跳过时段 (8:00-9:30)，等待...")
                # 每秒检查一次是否结束跳过时段或收到停止信号
                while skip_period_start <= datetime.now().time() <= skip_period_end:
                    if stop_event.is_set():
                        api_disconnect(api)
                        return
                    time.sleep(1)
                continue  # 跳过时段结束后继续主循环

            # 执行核心逻辑
            print(f"测试运行第{test_i}次")

            code_name_map_buy = apply_stock_filters_second(code_name_map, stock_require_data,api)
            add_to_monitoring_pool(code_name_map_buy,api)

            code_name_map_sell = apply_selling_stocks_second(code_name_map2, stock_require_data_sell,api)
            remove_stock_from_monitoring_pool(code_name_map_sell,api)



            # 每次循环后检查停止信号
            for _ in range(60):  # 每1秒检查一次，共60秒
                if stop_event.is_set():
                    api_disconnect(api)
                    break
                time.sleep(1)

        except Exception as e:
            print(f"执行出错: {e}")
            time.sleep(5)

        test_i = test_i + 1

    return