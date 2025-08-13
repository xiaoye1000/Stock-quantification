import pandas as pd
import os
import glob

#数据库
import sqlite3
from ..SQLbase.SQLite_manage import (
    get_data_dir,
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
        isbuy         INTEGER
    );
    """

    c.execute(create_table_sql)

    conn.commit()

    if keep_open:
        print("已创建数据库表")
        return conn
    else:
        print("已创建数据库（关闭连接模式）")
        conn.close()
        return None

#-----------------------------------------------------------------------
# 提取股票代码（保留市场前缀，去掉点）
def format_stock_code_for_tablename(formatted_code)-> str:
    """将格式化后的股票代码转换为表名格式（sh+6位数字或sz+6位数字）"""
    if '.' in formatted_code:
        prefix, suffix = formatted_code.split('.')
        return prefix + suffix
    else:
        # 如果没有点，尝试处理（如无法识别市场前缀的纯数字）
        if formatted_code.startswith('6'):
            return 'sh' + formatted_code
        elif formatted_code.startswith('0') or formatted_code.startswith('3'):
            return 'sz' + formatted_code
        else:
            return formatted_code  # 返回原始值

#获取xls路径
#内置函数，无需使用
def get_xls_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data/tradeData')
    os.makedirs(data_dir, exist_ok=True)  # 确保目录存在
    return os.path.normpath(data_dir)

# 证券代码格式化函数
#内置函数，无需使用
def format_stock_code(code)-> str:
    #将证券代码统一为sh./sz.前缀的6位标准格式
    code_str = str(code) if not isinstance(code, str) else code

    #清理特殊字符
    clean_code = ''.join(char for char in code_str if char.isdigit())

    # 补全缺失的零
    padded_code = clean_code.zfill(6)

    # 添加市场前缀
    if padded_code.startswith(('60', '68', '90', '58')):  # 沪市股票/科创板/B股/基金ETF
        return f"sh.{padded_code}"
    elif padded_code.startswith(('00', '30', '20', '159', '399')):  # 深市主板/创业板/B股/基金ETF
        return f"sz.{padded_code}"
    else:
        print(f"警告: 无法识别的证券代码格式: {code_str} -> {padded_code}")
        return padded_code  # 无法识别时返回原始6位数字

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
        print(f"xlsx方法读取失败: {str(e)},正在尝试其他方法")

    # 方法2：尝试CSV格式读取（文件可能是CSV格式但用了xls扩展名）
    try:
        # 尝试常见中文编码
        for encoding in ['gb2312', 'gbk', 'gb18030', 'utf-8']:
            try:
                # CSV可能用逗号、制表符或分号分隔
                return pd.read_csv(file_path, encoding=encoding, sep=None, engine='python')
            except Exception as e:
                print(f"错误: {str(e)}")
                continue
    except Exception as e:
        print(f"CSV方法失败: {str(e)},正在尝试其他方法")

    # 方法3：直接检查文件内容
    try:
        with open(file_path, 'rb') as f:
            header = f.read(10)
            print(f"文件头部内容: {header}")
            # 判断是否是文本文件
            try:
                text_content = header.decode('gbk')
                print(f"可能包含文本内容: {text_content}")
            except Exception as e:
                print(f"错误: {str(e)}")
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

    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, 'trade-data.db')

    # 调用创建数据库
    conn = create_trade_db(table_name, db_path, keep_open=True)

    if not xls_files:
        print(f"在 {target_dir} 中未找到任何Excel文件")
        conn.close()
        return

    for file_path in xls_files:

        filename = os.path.basename(file_path)
        print(f"\n处理文件: {filename}")

        # 使用多种方法尝试读取
        df = try_read_excel(file_path)

        if df is None:
            print(f"\n无法读取文件: {file_path}")
            continue

        # 成功读取文件
        print(f"\n成功读取: {filename}")
        print(f"数据形状: {df.shape} 行 x {df.shape[1]} 列")
        print("\n前2行数据:")
        print(df.head(2))

        # 数据处理逻辑
        try:
            # 1. 列名标准化处理
            column_mapping = {
                '成交日期': 'trade_date',
                '证券代码': 'code',
                '证券名称': 'code_name',
                '买卖标志': 'direction',
                '成交价格': 'trade_price',
                '成交数量': 'trade_number'
            }

            # 重命名列
            rename_dict = {}
            for col in df.columns:
                for chinese_col, english_col in column_mapping.items():
                    if chinese_col in col:
                        rename_dict[col] = english_col
            df = df.rename(columns=rename_dict)

            # 2. 处理买卖标志（买入=1，卖出=0）
            df['isbuy'] = df['direction'].apply(
                lambda x: 1 if '买入' in str(x) else 0 if '卖出' in str(x) else None
            )

            # 3. 日期格式统一（YYYYMMDD → YYYY-MM-DD）
            def format_date(date_val):
                try:
                    date_str = str(int(date_val))
                    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                except Exception as er:
                    print(f"日期重构失败: {str(er)}")
                    return date_val

            if 'trade_date' in df.columns:
                df['trade_date'] = df['trade_date'].apply(format_date)

            if 'code' in df.columns:
                df['code'] = df['code'].apply(format_stock_code)
            else:
                print("警告: 数据中缺少证券代码列")

            # 4. 选择需要的列
            req_cols = ['trade_date', 'code', 'code_name',
                        'trade_price', 'trade_number', 'isbuy']
            df = df[[col for col in req_cols if col in df.columns]]

            # 5. 插入数据库
            #获取代码
            trade_code=format_stock_code_for_tablename(str(df['code'][0]))
            #增加编号
            final_table_name = f"{table_name}_{trade_code}"

            df.to_sql(final_table_name, conn, if_exists='append', index=False)
            print(f"成功插入到数据库,名称为: {final_table_name}")

        except Exception as e:
            print(f"数据加入到数据库失败: {str(e)}")
            continue

    conn.close()
    print("=" * 50)
    print("读取文件到数据库函数运行结束")
