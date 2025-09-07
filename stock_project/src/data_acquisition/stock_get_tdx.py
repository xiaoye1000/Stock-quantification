#用于获取股票行情数据的函数

import pandas as pd
import os

#接口
import pytdx
from pytdx.hq import TdxHq_API

#json文件
import json

#数据库引用
from ..SQLbase.SQLite_manage import load_stock_mapping

#----------------------------------------------------------------------------
'''

'''
#转换为通达信的获取股票的形式
def change_szsh_to_tdx():
    # 加载股票代码-名称映射
    code_name_map = load_stock_mapping()

    return code_name_map

def pytdx_nowdata_stock():
    #加载通达信连接服务器
    api = TdxHq_API(heartbeat=True)
    #ip可以参考pytdx的各个服务器地址，多次尝试可用的
    api.connect('218.6.170.47', 7709)

    result = api.get_security_quotes([(0, '000001')])
    result = api.to_df(result)
    print(result)

    api.disconnect()
    return
