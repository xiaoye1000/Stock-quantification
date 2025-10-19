#运行函数

import time

#多头择时策略
from .stock_strategy.DTZS_strategy import *

from .src.data_acquisition.get_stock_pool import *

#补充数据
from .src.data_acquisition.stock_data_complement import data_complement


def dtzs_run(stop_event):
    #更新股票池
    get_all_stock_to_pool()

    #自动补全数据
    data_complement()

    #一筛，预处理
    code_name_map, stock_require_data = apply_stock_filters_first(get_all_stock_code())

    # 无限循环部分（可随时停止）
    while not stop_event.is_set():
        try:
            # 执行核心逻辑
            apply_stock_filters_second(code_name_map, stock_require_data)
            add_to_monitoring_pool(code_name_map)

            # 每次循环后检查停止信号
            for _ in range(60):  # 每1秒检查一次，共60秒
                if stop_event.is_set():
                    break
                time.sleep(1)

        except Exception as e:
            print(f"执行出错: {e}")
            time.sleep(5)

    return