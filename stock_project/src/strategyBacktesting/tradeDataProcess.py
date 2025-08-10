import pandas as pd
import os
import glob

from datetime import datetime

#数据库
import sqlite3
from ..SQLbase.SQLite_manage import (
    get_data_dir
)

#-----------------------------------------------------------------------
# 数据库文件固定存储在trade-data.db中
# 内置函数，无需使用
def create_trade_db(table_name, db_path, keep_open=False):
    conn = sqlite3.connect(db_path)

    # cursor对象
    c = conn.cursor()

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        trade_date    TEXT    NOT NULL,
        code          TEXT    NOT NULL,
        code_name     TEXT,
        trade_price   REAL,
        trade_number  REAL,
        isbuy         INTEGER,
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

def trade_to_sql_for(table_name):
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, 'trade-data.db')

    # 调用创建数据库
    con_name = create_trade_db(table_name, db_path, keep_open=True)
#-----------------------------------------------------------------------
#获取xls路径
#内置函数，无需使用
def get_xls_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data/tradeData')
    os.makedirs(data_dir, exist_ok=True)  # 确保目录存在
    return os.path.normpath(data_dir)

#尝试多种方式读取Excel文件
#内置函数
def try_read_excel(file_path):
    # 尝试用xlsx方法读取
    try:
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path, engine='openpyxl')
        else:
            return pd.read_excel(file_path, engine='xlrd')
    except Exception as e:
        print(f"xlsx方法读取失败: {str(e)}")

    # 方法2：尝试CSV格式读取（文件可能是CSV格式但用了xls扩展名）
    try:
        # 尝试常见中文编码
        for encoding in ['gb2312', 'gbk', 'gb18030', 'utf-8']:
            try:
                # CSV可能用逗号、制表符或分号分隔
                return pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
            except:
                continue
    except Exception as e:
        print(f"CSV方法失败: {str(e)}")

    # 方法3：直接检查文件内容
    try:
        with open(file_path, 'rb') as f:
            header = f.read(10)
            print(f"文件头部内容: {header}")
            # 判断是否是文本文件
            try:
                text_content = header.decode('gbk')
                print(f"可能包含文本内容: {text_content}")
            except:
                pass

            # 尝试更多格式的可能性
            if b'PDF' in header:
                print("警告: 文件看起来像是PDF格式!")
            elif b'html' in header.lower():
                print("警告: 文件看起来像是HTML格式!")
    except Exception as e:
        print(f"文件检查失败: {str(e)}")

    return None


def process_xls_files(table_name):
    #连接文档所在数据，xls或xlsx
    target_dir = get_xls_dir()
    print(f"扫描目录: {target_dir}")

    xls_files = glob.glob(os.path.join(target_dir, '*.xls*'))

    trade_to_sql_for(table_name)

    if not xls_files:
        print(f"在 {target_dir} 中未找到任何Excel文件")
        return

    for file_path in xls_files:
        filename = os.path.basename(file_path)
        print(f"\n处理文件: {filename}")

        # 使用多种方法尝试读取
        df = try_read_excel(file_path)

        if df is None:
            print(f"\n无法读取文件: {file_path}")
            print("可能原因:")
            print("1. 文件格式错误或已损坏")
            print("2. 文件实际上是文本文件（如CSV）而非Excel")
            print("3. 文件是其他格式（如PDF, HTML）")
            print("4. 使用了不支持的Excel格式（如WPS生成的文件）")
            print("=" * 50)
            continue

        # 成功读取文件
        print(f"\n成功读取: {filename}")
        print(f"数据形状: {df.shape} 行 x {df.shape[1]} 列")
        print("\n列名:", df.columns.tolist())
        print("\n前2行数据:")
        print(df.head(2))

    print("=" * 50)
    print("读取运行结束")
