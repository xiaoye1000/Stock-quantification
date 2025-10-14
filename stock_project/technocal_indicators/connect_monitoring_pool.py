import os
import csv
from datetime import datetime


def connect_monitoring_pool(code_name_map, now_price):
    # 确定目标文件夹路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'stock_project', 'data', 'monitoring_pool')

    # 如果目标文件夹不存在，则创建
    os.makedirs(data_dir, exist_ok=True)

    pool_file = os.path.join(data_dir, 'monitoring_pool.csv')
    history_file = os.path.join(data_dir, 'monitoring_history.csv')

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 情况1: 监控池文件不存在（首次运行）
    if not os.path.exists(pool_file):
    # 创建监控池文件并写入标题行
        with open(pool_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['stock_code', 'stock_name', 'entry_time', 'entry_price'])

            # 写入所有股票数据
            for code, name in code_name_map.items():
                # 获取当前价格，如果now_price中没有该股票代码，则用None表示
                price = now_price.get(code, None)
                writer.writerow([code, name, current_time, price])
        return None

    # 情况2: 监控池文件已存在
    # 读取现有监控池数据，构建现有股票代码集合
    existing_codes = set()
    # 我们不需要修改现有数据，只需要检查哪些是新增的
    with open(pool_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['stock_code']
            existing_codes.add(code)

    # 获取当前股票代码集合
    current_codes = set(code_name_map.keys())

    # 计算新增的股票代码（当前有但监控池中没有的）
    added_codes = current_codes - existing_codes

    # 处理新增的股票
    if added_codes:
        # 将新增股票追加到监控池文件
        with open(pool_file, 'a', newline='', encoding='utf-8') as f_pool:
            writer_pool = csv.writer(f_pool)
            for code in added_codes:
                name = code_name_map[code]
                price = now_price.get(code, None)
                writer_pool.writerow([code, name, current_time, price])

        # 将新增股票记录到历史文件（入池记录）
        with open(history_file, 'a', newline='', encoding='utf-8') as f_hist:
            writer_hist = csv.writer(f_hist)
            # 如果历史文件不存在，则写入标题行
            if not os.path.exists(history_file) or os.path.getsize(history_file) == 0:
                writer_hist.writerow(['stock_code', 'stock_name', 'action', 'time', 'price'])

            for code in added_codes:
                name = code_name_map[code]
                price = now_price.get(code, None)
                writer_hist.writerow([code, name, 'entry', current_time, price])

    return None


def get_monitoring_pool():
    # 确定目标文件夹路径
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'stock_project', 'data', 'monitoring_pool')
    pool_file = os.path.join(data_dir, 'monitoring_pool.csv')

    # 如果监控池文件不存在，返回空字典
    if not os.path.exists(pool_file):
        return {}

    # 读取监控池文件
    code_name_map = {}
    with open(pool_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['stock_code']
            name = row['stock_name']
            code_name_map[code] = name

    return code_name_map