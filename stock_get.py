#!/usr/bin/env python
# coding: utf-8

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

#基于Tushare Pro的股票日线行情数据获取
#已对输出结果进行规整化，若token或API不可用，请使用其他函数
@handle_api_errors

def pro_daily_stock(code_val,start_val,end_val):
    #Token接口API值
    token = ""
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

#基于Baostock的股票日线行情数据获取
#已对输出结果进行规整化
@handle_api_errors

def bs_daily_stock(code_val,start_val,end_val,adjust_val='2'):
    #### 登陆系统 ####
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

    #处理格式
    result.close = result.close.astype('float64')
    result.open = result.open.astype('float64')
    result.low = result.low.astype('float64')
    result.high = result.high.astype('float64')
    result.volume = result.volume.astype('float64')
    result.volume = result.volume/100 #单位转换每股和每手
    
    #处理索引时间
    result.date = pd.DatetimeIndex(result.date)
    result.set_index("date",drop=True,inplace=True)
    result.index = result.index.set_names('Date')
    
    #规整化列索引
    recon_data = {'High':result.high,'Low':result.low,'Open':result.open,'Close':result.close,'Volume':result.volume}
    df_recon = pd.DataFrame(recon_data)
    
    #退出系统
    bs.logout()
    return df_recon