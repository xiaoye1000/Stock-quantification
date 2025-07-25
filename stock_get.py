#!/usr/bin/env python
# coding: utf-8

#用于获取股票行情数据的函数

import pandas as pd
import datetime
import tushare as ts
import baostock as bs
from functools import wraps

#异常处理
def handle_api_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ts.exception.RequestError as e:
            print(f"Tushare API错误: {str(e)}")
        except bs.common.exception.BaostockException as e:
            print(f"Baostock 错误: {str(e)}")
        except ValueError as e:
            print(f"参数错误: {str(e)}")
        except Exception as e:
            print(f"处理股票数据时发生错误: {str(e)}")
        return None
    return wrapper

'''
基于Tushare Pro的股票日线行情数据获取
已对输出结果进行规整化，若token或API不可用，请使用其他函数

输入值：
code_val:股票代码后加.SH（上证股票）或.SZ（深证股票）
start_val,end_val:格式为YYYYMMDD形式的日期

注意：使用Tushare需要注册并自带API，并且需要积分解锁功能，建议使用Baostock
'''
@handle_api_errors

def pro_daily_stock(code_val,start_val,end_val):
    #Token接口API值
    token = ''
    pro = ts.pro_api(token)
    
    #Tushare获取股票信息
    df_stock = pro.daily(ts_code=code_val,start_date=start_val,end_date=end_val)
    
    #规整化，转变为标准索引
    df_stock.trade_date = pd.DatetimeIndex(df_stock.trade_date)
    df_stock.set_index("trade_date",drop=True,inplace=True)
    
    #规整化，调整行索引排序
    df_stock.sort_index(inplace=True)
    
    #设置行索引名为Date
    df_stock.index = df_stock.index.set_names('Date')
    
    #规整化列索引
    recon_data = {'High':df_stock.high,'Low':df_stock.low,'Open':df_stock.open,'Close':df_stock.close,'Volume':df_stock.vol}
    df_recon = pd.DataFrame(recon_data)
    
    return df_recon

'''
基于Baostock的股票日线行情数据获取

对输出结果进行规整化的函数：
以时间为pd索引，返回最高价，最低价，开盘价，收盘价，成交量(转换为手)

输入值：
code_val:sh.（上海）或sz.（深圳）加股票代码
start_val,end_val:格式为YYYY-MM-DD形式的日期
adjust_val: 2:默认前复权 1:后复权 3:不复权
already_login：是否需要登入，默认需要，在外部代码登入可以减少运行时间
'''
@handle_api_errors

def bs_daily_stock(code_val,start_val,end_val,adjust_val='2',already_login=False):
    #### 登陆系统 ####
    if already_login==False:
        lg = bs.login()
    
    #获取历史行情数据
    freq_val='d'#日k线
    fields = "date,open,high,low,close,volume"
    df_bs = bs.query_history_k_data_plus(code_val,fields,start_date=start_val,end_date=end_val,frequency=freq_val, adjustflag=adjust_val)
    #adjustflag 2:默认前复权 1:后复权 3:不复权

    data_list=[]

    #合并数据为DataFrame
    while (df_bs.error_code == '0') & df_bs.next():
        data_list.append(df_bs.get_row_data())
    result = pd.DataFrame(data_list, columns=df_bs.fields)

    #数据处理
    numeric_cols = ['close','open','low','high','volume']
    for col in numeric_cols:
        result[col] = pd.to_numeric(result[col], errors='coerce')  # 安全转换，处理空值
    
    result.volume = result.volume/100 #单位转换每股和每手
    
    #处理索引时间
    result.date = pd.DatetimeIndex(result.date)
    result.set_index("date",drop=True,inplace=True)
    result.index = result.index.set_names('Date')
    
    #规整化列索引
    recon_data = {'High':result.high,'Low':result.low,'Open':result.open,'Close':result.close,'Volume':result.volume}
    df_recon = pd.DataFrame(recon_data)
    
    #退出系统
    if already_login==False:
        bs.logout()
    return df_recon


'''
基于Baostock的股票日线行情数据获取2

输出结果为原式格式的函数（可以参考Baostock文档）：
date:交易所行情日期
code:证券代码
open:开盘价
high:最高价
low:最低价
close:收盘价
preclose:前收盘价（当日发生除权除息时，“前收盘价”不是前一天的实际收盘价）
volume:成交量（累计 单位：股）
amount:成交额（单位：人民币元）
adjustflag:复权状态(1：后复权， 2：前复权，3：不复权）
turn:换手率
tradestatus:交易状态(1：正常交易 0：停牌）
pctChg:涨跌幅（百分比）
peTTM:滚动市盈率
pbMRQ:市净率
psTTM:滚动市销率
pcfNcfTTM:滚动市现率
isST:是否ST股，1是，0否


输入值：
code_val:sh.（上海）或sz.（深圳）加股票代码
start_val,end_val:格式为YYYY-MM-DD形式的日期
adjust_val: 2:默认前复权 1:后复权 3:不复权
already_login：是否需要登入，默认需要，在外部代码登入可以减少运行时间
'''
@handle_api_errors

def bs_daily_original_stock(code_val,start_val,end_val,adjust_val='2',already_login=False):
    #### 登陆系统 ####
    if already_login==False:
        lg = bs.login()
    
    #获取历史行情数据
    freq_val='d'#日k线
    fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
    df_bs = bs.query_history_k_data_plus(code_val,fields,start_date=start_val,end_date=end_val,frequency=freq_val, adjustflag=adjust_val)
    #adjustflag 2:默认前复权 1:后复权 3:不复权

    data_list=[]

    #合并数据为DataFrame
    while (df_bs.error_code == '0') & df_bs.next():
        data_list.append(df_bs.get_row_data())
    result = pd.DataFrame(data_list, columns=df_bs.fields)

    #退出系统
    if already_login==False:
        bs.logout()
    return result