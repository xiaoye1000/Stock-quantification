#用于股票的数据库存储相关的函数

import pandas as pd
import time
import os

#json文件
import json

#baostock部分
import baostock as bs
from ..data_acquisition.stock_get import bs_daily_original_stock

#数据库
import sqlite3

#类型整合
from typing import Union

#获取数据路径
#内置函数，无需使用
def get_data_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data')
    os.makedirs(data_dir, exist_ok=True)  # 确保目录存在
    return data_dir

#读取json文件
#需要先运行生成股票池get_stock_pool，确保有stock_pool.json获取所有股票/指数
#内置函数，无需使用
def json_to_str():
    # 获取数据目录
    data_dir = get_data_dir()
    json_path = os.path.join(data_dir, 'stock_pool.json') 
    
    with open(json_path,"r",encoding='utf-8') as load_f:
        stock_index = json.load(load_f)
    return stock_index

#连接/创建数据库
#数据库文件固定存储在stock-data.db中
#内置函数，无需使用
def create_stock_db(table_name,db_path,keep_open=False):
    
    conn = sqlite3.connect(db_path)

    #cursor对象
    c = conn.cursor()

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date          TEXT    NOT NULL,
        code          TEXT    NOT NULL,
        code_name     TEXT,
        open          REAL,
        high          REAL,
        low           REAL,
        close         REAL,
        preclose      REAL,
        volume        REAL,
        amount        REAL,
        adjustflag    INTEGER,
        turn          REAL,
        tradestatus   INTEGER,
        pctChg        REAL,
        isST          INTEGER,
        PRIMARY KEY (date, code)
    );
    """
    
    c.execute(create_table_sql)

    conn.commit()
    
    if keep_open:
        print(f"已创建数据库表: {table_name}")
        return conn 
    else:
        print("已创建数据库（关闭连接模式）")
        conn.close()
        return None

# 从JSON文件加载股票代码和名称映射
def load_stock_mapping(json_path=None):
    if json_path is None:
        data_dir = get_data_dir()
        json_path = os.path.join(data_dir, 'stock_pool.json')
        
    with open(json_path, 'r', encoding='utf-8') as f:
        stock_data = json.load(f)
    
    # 创建代码到名称的映射字典
    code_name_map = {}
    for category, stocks in stock_data.items():
        # 只处理股票类型
        if category == '股票':
            for name, code in stocks.items():
                code_name_map[code] = name
    
    return code_name_map

#json数据存入到数据库
#table_name自选池名称
#start,end:格式为YYYY-MM-DD形式的日期
def stock_to_sql_for(table_name,start,end):
    # 获取数据库路径
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, 'stock-data.db')
    
    #调用创建数据库
    con_name=create_stock_db(table_name, db_path, keep_open=True)
    
    # 加载股票代码-名称映射
    code_name_map = load_stock_mapping()
    
    #调用读取json
    stock_code = json_to_str()
    
    bs.login()
    
    for code in list(stock_code['股票'].values()):
        try:
            #调用原始数据读取
            data = bs_daily_original_stock(code,start,end,adjust_val='2',already_login=True)
            #股票名称
            stock_name = code_name_map.get(code, "未知股票")
            data['code_name'] = stock_name
            time.sleep(0.2)
            data.to_sql(table_name,con_name,index=False,if_exists='append')#存到数据库
            print("right code is %s"%code)
        except Exception as e:
            print("error code is %s"%code)
            print(f"错误，检查是否已有数据或程序错误:{str(e)}")
    
    bs.logout()
    
    #关闭数据库
    print("导入数据库完成")
    con_name.close()
    print(f"数据已保存到: {db_path}")
#----------------------------------------------------------
#删除表函数
#table_name自选池名称
def _drop_table(db_file: str, table_name: str) -> str:
    # 获取数据库路径
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, db_file)
    
    conn = None
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 检查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not c.fetchone():
            return f"表 '{table_name}' 不存在"

        #删除整个表
        c.execute(f"drop table {table_name}")
        conn.commit()
        return f"表 '{table_name}' 已从 [{db_file}] 中成功删除"
    
    except sqlite3.Error as e:
        return f"删除表时出错: {str(e)}"
    finally:
        if conn:
            conn.close()

# 交易数据库专用接口
def drop_trade_table(table_name: str) -> str:
    """专用于trade-data数据库的删除函数"""
    return _drop_table("trade-data.db", table_name)

# 原股票数据库接口
def drop_stock_table(table_name: str) -> str:
    """专用于stock-data数据库的删除函数"""
    return _drop_table("stock-data.db", table_name)

#----------------------------------------------------------
#查询表所有的值的函数
#table_name自选池名称
def _query_table(db_file: str, table_name: str) -> Union[pd.DataFrame, str]:
    # 获取数据库路径
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, db_file)
    
    conn = None
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 检查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not c.fetchone():
            return f"表 '{table_name}' 不存在"
        
        #读取数据
        df=pd.read_sql_query(f"select * from {table_name}",conn)
        return df
    except sqlite3.Error as e:
        return f"读取表时出错: {str(e)}"
    finally:
        if conn:
            conn.close()

# 交易数据库查询
def query_trade_table(table_name: str) -> Union[pd.DataFrame, str]:
    """专用函数：查询trade-data.db中的表数据"""
    return _query_table("trade-data.db", table_name)

# 股票数据库查询
def query_stock_table(table_name: str) -> Union[pd.DataFrame, str]:
    """专用函数：查询stock-data.db中的表数据"""
    return _query_table("stock-data.db", table_name)