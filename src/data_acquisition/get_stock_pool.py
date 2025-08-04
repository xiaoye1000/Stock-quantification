#!/usr/bin/env python
# coding: utf-8

#用于获取/更新当前市场的指数、个股、转债
#过滤已退市的个股
#结果存储在stock_pool.json

import json
import pandas as pd
import datetime
import tushare as ts
import baostock as bs


print('执行Baostock的全行情获取')
# 登陆系统
lg = bs.login()

# 显示登陆返回信息
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

rs = bs.query_stock_basic()

# 打印结果集
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

# 登出系统
bs.logout()


# 筛选outDate为空的记录，即未退市的股票
result = result[result['outDate'] == '']


# 按类型分类存储
stock_index = {
    '股票': dict(zip(result[result['type'] == '1']['code_name'], 
                result[result['type'] == '1']['code'])),
    '指数': dict(zip(result[result['type'] == '2']['code_name'], 
                result[result['type'] == '2']['code'])),
    '其他': dict(zip(result[result['type'] == '3']['code_name'], 
                result[result['type'] == '3']['code'])),
    '可转债': dict(zip(result[result['type'] == '4']['code_name'], 
                result[result['type'] == '4']['code'])),
    'ETF': dict(zip(result[result['type'] == '5']['code_name'], 
                result[result['type'] == '5']['code']))
}


#将数据写入json文件中
with open("stock_pool.json","w",encoding='utf-8') as f:
    json.dump(stock_index,f,ensure_ascii=False,indent=4)

print('完成：获取/更新当前市场的指数、个股、转债')