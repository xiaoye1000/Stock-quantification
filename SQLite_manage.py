#!/usr/bin/env python
# coding: utf-8

#用于股票的数据库存储相关的函数

import pandas as pd
import time

#json文件
import json

#baostock部分
import baostock as bs
from stock_get import bs_daily_original_stock

#数据库
import sqlite3

#读取json文件
#需要先运行生成股票池get_stock_pool，确保有stock_pool.json获取所有股票/指数
#内置函数，无需使用
def json_to_str():
    with open("stock_pool.json","r",encoding='utf-8') as load_f:
        stock_index = json.load(load_f)
    return stock_index

#连接/创建数据库
#数据库文件固定存储在stock-data.db中
#内置函数，无需使用
def create_stock_db(table_name,db_path='stock-data.db',keep_open=False):
    conn = sqlite3.connect(db_path)

    #cursor对象
    c = conn.cursor()

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date          TEXT    NOT NULL,
        code          TEXT    NOT NULL,
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

    conn.commit
    
    if keep_open:
        print("已创建数据库")
        return conn  # 返回连接对象供后续使用
    else:
        print("已创建数据库（关闭连接模式）")
        conn.close()
        return None

#json数据存入到数据库
#table_name自选池名称
#start,end:格式为YYYY-MM-DD形式的日期
def stock_to_sql_for(table_name,start,end):
    
    #调用创建数据库
    con_name=create_stock_db(table_name,db_path='stock-data.db',keep_open=True)
    
    #调用读取json
    stock_code = json_to_str()
    
    lg = bs.login()
    
    for code in list(stock_code['股票'].values()):
        try:
            #调用原始数据读取
            data = bs_daily_original_stock(code,start,end,adjust_val='2',already_login=True)
            time.sleep(0.2)
            data.to_sql(table_name,con_name,index=False,if_exists='append')#存到数据库
            print("right code is %s"%code)
        except:
            print("error code is %s"%code)
            print("错误，检查是否已有数据或程序错误")
    
    bs.logout()
    
    #关闭数据库
    print("导入数据库完成")
    con_name.close()

#删除表函数
#table_name自选池名称
def sql_drop_table(table_name):
    db_path='stock-data.db'
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
        return f"表 '{table_name}' 已成功删除"
    
    except sqlite3.Error as e:
        return f"删除表时出错: {str(e)}"
    finally:
        if conn:
            conn.close()

#查询表函数
#table_name自选池名称
def sql_query_table(table_name):
    db_path='stock-data.db'
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