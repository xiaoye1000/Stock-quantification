#用于获取股票行情数据的函数

import pandas as pd
import os

#接口
import pytdx
from pytdx.hq import TdxHq_API

#数据库引用
from ..SQLbase.SQLite_manage import load_stock_mapping

#----------------------------------------------------------------------------
'''
pytdx的获取股票数据的接口
模拟通达信连接服务器发送请求，返回各种股票数据

返回值：
market：1为上证市场，0为深证市场
code：股票代码
price:当前价
last_code：昨收价
open:开盘价
high:当日当前时间最高价
low:当日当前时间最低价
servertime：数据时间戳，交易所服务器生成该数据记录的时间
vol:当日截止当前时间成交量（手）
cur_vol:最近一笔成交量(手)
amount:当日截至当前时间的总成交金额
s_vol:主动卖出成交的总手数，也称内盘
b_vol:主动买入成交的总手数，也称外盘
bid1- bid5:买一价 至 买五价
ask1- ask5:卖一价 至 卖五价
bid_vol1- bid_vol5:买一量 至 买五量（手）
ask_vol1- ask_vol5:卖一量 至 卖五量（手）

以下返回值没有什么参考意义，可以忽略
reversed_bytesX
active1/2：疑似交易所状态代码

'''
#转换为通达信的获取股票的形式
def change_szsh_to_tdx():
    # 加载股票代码-名称映射
    code_name_map = load_stock_mapping()
    # 转换数据结构
    tdx_list = []
    for full_code in code_name_map.keys():
        # 分割市场代码和股票代码
        exchange, code = full_code.split('.')

        # 转换交易所标识 (sh->1, sz->0)
        market = 1 if exchange == 'sh' else 0 if exchange == 'sz' else None

        # 仅处理有效的交易所代码
        if market is not None:
            # 确保股票代码为6位字符串
            tdx_list.append((market, code))

    return tdx_list

def api_disconnect(api):
    api.disconnect()
    return None

#连接函数，避免重复连接服务器
def connect_tdx():
    #加载通达信连接服务器
    api = TdxHq_API(heartbeat=True)
    #ip可以参考pytdx的各个服务器地址，多次尝试可用的
    #这里给出若干可用的ip作备用
    ips = [
        ('218.6.170.47', 7709),  # 上证云成都电信一
        ('123.125.108.14', 7709),  # 上证云北京联通一
        ('180.153.18.170', 7709),  # 上海电信主站Z1
        ('180.153.18.172', 80),  # 上海电信主站Z80
        ('202.108.253.139', 80),  # 北京联通主站Z80
        ('60.191.117.167', 7709),  # 杭州电信主站J1
    ]

    #尝试连接
    for ip, port in ips:
        try:
            api.connect(ip, port, time_out=1.5)
            print(f"成功连接到服务器: {ip}:{port}")
            return api
        except Exception as e:
            print(f"连接失败 {ip}:{port} - {str(e)}")
    print("所有服务器连接失败，请检查网络")
    return None

def pytdx_nowdata_stock():
    # 连接服务器
    api = connect_tdx()
    if api is None:
        return pd.DataFrame()

    #获取表单
    tdx_list = change_szsh_to_tdx()

    # 分批获取数据（每次最多80只股票）
    batch_size = 80
    all_data = []
    total_stocks = len(tdx_list)
    batch_count = (total_stocks + batch_size - 1) // batch_size

    for batch_idx in range(batch_count):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_stocks)
        batch = tdx_list[start_idx:end_idx]

        try:
            result = api.get_security_quotes(batch)
            if result:
                df_batch = api.to_df(result)
                all_data.append(df_batch)
                print(f"已获取批次 {batch_idx + 1}/{batch_count} 数据，包含 {len(df_batch)} 条记录")
            else:
                print(f"批次 {batch_idx + 1}/{batch_count} 返回空数据，开始逐个获取...")

                # 逐个获取该批次内的股票
                single_success = 0
                single_failed = []

                for market, code in batch:
                    try:
                        single_result = api.get_security_quotes([(market, code)])
                        if single_result:
                            df_single = api.to_df(single_result)
                            all_data.append(df_single)
                            single_success += 1
                        else:
                            single_failed.append(f"{'sh' if market == 1 else 'sz'}.{code}")
                    except Exception as e:
                        single_failed.append(f"{'sh' if market == 1 else 'sz'}.{code} ({str(e)})")

                # 输出单个获取结果
                print(f"  单个获取完成: 成功 {single_success} 只, 失败 {len(single_failed)} 只")
                if single_failed:
                    print(f"  失败股票列表: {', '.join(single_failed[:5])}{'...' if len(single_failed) > 5 else ''}")

        except Exception as e:
            print(f"获取批次 {batch_idx + 1}/{batch_count} 数据时出错: {str(e)}")
            print(f"  尝试逐个获取该批次股票...")

            # 逐个获取该批次内的股票
            single_success = 0
            single_failed = []

            for market, code in batch:
                try:
                    single_result = api.get_security_quotes([(market, code)])
                    if single_result:
                        df_single = api.to_df(single_result)
                        all_data.append(df_single)
                        single_success += 1
                    else:
                        single_failed.append(f"{'sh' if market == 1 else 'sz'}.{code}")
                except Exception as e2:
                    single_failed.append(f"{'sh' if market == 1 else 'sz'}.{code} ({str(e2)})")

            # 输出单个获取结果
            print(f"  单个获取完成: 成功 {single_success} 只, 失败 {len(single_failed)} 只")
            if single_failed:
                print(f"  失败股票列表: {', '.join(single_failed[:5])}{'...' if len(single_failed) > 5 else ''}")

    api_disconnect(api)

    # 合并所有批次数据
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"成功获取 {len(final_df)} 条股票数据")

        # 预处理，删除不需要的列
        cols_to_drop = [f'reversed_bytes{i}' for i in range(10)] + ['active1', 'active2']
        final_df = final_df.drop(columns=cols_to_drop, errors='ignore')  # 忽略不存在的列

        # 保存到CSV文件
        #filename = f"stock_quotes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        #final_df.to_csv(filename, index=False, encoding='utf-8-sig')
        #print(f"数据已保存到 {filename}")

        return final_df

    else:
        print("未获取到任何数据")
        return pd.DataFrame()