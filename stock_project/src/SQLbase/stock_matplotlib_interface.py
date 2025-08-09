#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os

#数据库
import sqlite3

#绘图
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

#k线
import mpl_finance as mpf

#TA-Lib
import talib
from talib import MA_Type #枚举MA_Type类型

#获取数据路径
#内置函数，无需使用
def get_data_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data')
    os.makedirs(data_dir, exist_ok=True)  # 确保目录存在
    return data_dir

#将各种不同类型的图表函数注册到该容器中，方便调用
#内部函数
class DefTypesPool:
    #构造函数
    def __init__(self):
        self.routes = {}
        
    #装饰器函数，将各种绘图函数注册至self.routes
    def route_types(self,types_str):
        def decorator(f):
            self.routes[types_str] = f
            return f
        return decorator
    
    #根据路径输出已注册的函数
    def route_output(self, path):
        function_val = self.routes.get(path)
        if function_val:
            return function_val
        else:
            raise ValueError('Route "{}"" has not been registered'.format(path))

#实现各种类型的指标函数绘制
#内部函数
class MplTypesDraw:

    """
    df_index: 时间序列索引
    df_dat: 数据
    graph: matplotlib的axes对象
    """

    #实例化DefTypesPool
    mpl = DefTypesPool()

    #-------------------------------------------
    #使用装饰器，注册到self.routes中
    #折线图
    @mpl.route_types(u"line")
    def line_plot(self,df_index, df_dat, graph):
        # 绘制line图
        for key, val in df_dat.items():
            graph.plot(np.arange(0, len(val)), val, label=key, lw=1.0)
    
    #-------------------------------------------
    # 绘制ochl图(k线)
    @mpl.route_types(u"ochl")
    def ochl_plot(self,df_index, df_dat, graph):
        # 方案一
        #mpf.candlestick2_ochl(graph, df_dat['open'], df_dat['close'], df_dat['high'], df_dat['low'], width=0.5,
        #                      colorup='r', colordown='g') # 绘制K线走势
        # 方案二
        ohlc = list(zip(np.arange(0,len(df_index)),df_dat['open'], df_dat['close'], df_dat['high'], df_dat['low'])) # 使用zip方法生成数据列表
        mpf.candlestick_ochl(graph, ohlc, width=0.2, colorup='r', colordown='g', alpha=1.0) # 绘制K线走势
    
    #-------------------------------------------
    #柱状图（成交量）
    @mpl.route_types(u"bar")
    def bar_plot(self,df_index, df_dat, graph):
        #graph.bar(np.arange(0, len(df_index)), df_dat['Volume'], \
        #         color=['g' if df_dat['Open'][x] > df_dat['Close'][x] else 'r' for x in range(0,len(df_index))])

        graph.bar(np.arange(0, len(df_index)), df_dat['bar_red'], facecolor='red')
        graph.bar(np.arange(0, len(df_index)), df_dat['bar_green'], facecolor='green')
        
    #-------------------------------------------
    # 移动平均线（均线）
    @mpl.route_types(u"hline")
    def hline_plot(self,df_index, df_dat, graph):
        #子图上绘制
        for key, val in df_dat.items():
            graph.axhline(val['pos'], c=val['c'], label=key)
     
    #-------------------------------------------
    #金叉/死叉标注点
    @mpl.route_types(u"annotate")
    def annotate_plot(self,df_index, df_dat, graph):
        #外层循环每种标注类型
        for key, val in df_dat.items():
            #内层循环每个标注点
            for kl_index, today in val['andata'].iterrows():
                #标注点计算
                x_posit = df_index.get_loc(kl_index)
                graph.annotate(u"{}\n{}".format(key, today.name.strftime("%m.%d")),
                                   xy=(x_posit, today[val['xy_y']]),
                                   xycoords='data',
                                   xytext=(val['xytext'][0], val['xytext'][1]),
                                   va=val['va'],  # 点在标注下方
                                   textcoords='offset points',
                                   fontsize=val['fontsize'],
                                   arrowprops=val['arrow'])
    
    #-------------------------------------------
    #黄金分割线(水平线)
    @mpl.route_types(u"hline")
    def hline_plot(self,df_index, df_dat, graph):
        for key, val in df_dat.items():
            graph.axhline(val['pos'], c=val['c'], label=key)

#绘制完整的图表
class MplVisualIf(MplTypesDraw):

    #构造函数
    def __init__(self):
        MplTypesDraw.__init__(self)

    #由fig_output调用的子函数，用于创建对象和子图
    def fig_creat(self, **kwargs):
        if 'figsize' in kwargs.keys():# 创建fig对象
            self.fig = plt.figure(figsize=kwargs['figsize'], dpi=100, facecolor="white")
        else:
            self.fig = plt.figure(figsize=(14, 7), dpi=100, facecolor="white")
            
        # 创建子图
        self.graph = self.fig.add_subplot(1, 1, 1) 
        # 避免x轴日期刻度标签的重叠 将每个ticker标签倾斜45度
        self.fig.autofmt_xdate(rotation=45)  

    #由fig_output调用的子函数，用于设置图表的属性
    def fig_config(self, **kwargs):
        
        #图例设置
        if 'legend' in kwargs.keys():
            self.graph.legend(loc=kwargs['legend'], shadow=True)
        
        #坐标轴标签
        if 'xlabel' in kwargs.keys():
            self.graph.set_xlabel(kwargs['xlabel'])
        else:
            self.graph.set_xlabel(u"日期")
        self.graph.set_title(kwargs['title'])
        self.graph.set_ylabel(kwargs['ylabel'])
        
        #坐标轴范围
        self.graph.set_xlim(0, len(self.index)) # 设置x轴的范围

        if 'ylim' in kwargs.keys(): # 设置y轴的范围
            bottom_lim = self.graph.get_ylim()[0]# 获取当前y轴下限
            top_lim = self.graph.get_ylim()[1]# 获取当前y轴上限
            range_lim = top_lim - bottom_lim #计算y轴范围
            # 按比例调整y轴范围
            self.graph.set_ylim(bottom_lim+range_lim*kwargs['ylim'][0],
                                top_lim+range_lim*kwargs['ylim'][1])

        #刻度设置
        if 'xticks' in kwargs.keys(): # X轴刻度设定
            self.graph.set_xticks(range(0, len(self.index), kwargs['xticks']))
        else:
            self.graph.set_xticks(range(0, len(self.index), 15)) # 默认每15天标一个日期
            
        #刻度标签
        if 'xticklabels' in kwargs.keys(): # 标签设置为日期
            self.graph.set_xticklabels([self.index.strftime(kwargs['xticklabels'])[index]
                                        for index in self.graph.get_xticks()])
        else:
            self.graph.set_xticklabels([self.index.strftime('%Y-%m-%d')[index]
                                        for index in self.graph.get_xticks()])
            
    #调由fig_output调用的子函数,用show显示
    def fig_show(self, **kwargs):
        plt.show()

    #核心输出
    def fig_output(self, **kwargs):
        self.index = kwargs['index']# 设置数据索引（通常是时间序列）
        self.fig_creat(**kwargs)# 创建图表基础框架
        
        # 遍历所有需要绘制的图表类型
        for path, val in kwargs['draw_kind'].items():
            print(u"输出[%s]可视化图表:" % path)
            view_function = self.mpl.route_output(path)# 通过路由获取对应绘图函数
            view_function(self.index, val, self.graph)# 执行绘图
        
        self.fig_config(**kwargs)# 配置图表属性
        self.fig_show(**kwargs)# 显示图表

#-------------------------------------------------------------------------------------
#基础预设函数
#在绘制各种图之前调用该函数完成基础的预设，获取数据等
def basic_set_plot_stock(table_name, stock_code,start=None, end=None):
    # 基础配置
    plt.rcParams['font.sans-serif'] = ['SimHei'] 
    plt.rcParams['axes.unicode_minus'] = False
    
    stock_dat = pd.DataFrame()
    full_name = f"{stock_code} (未知股票)"  # 默认名称

    # 获取数据库路径
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, 'stock-data.db')

    #注意需要先生成数据库
    #连接/创建数据库
    conn = sqlite3.connect(db_path)
    
    try:
        # 获取股票名称
        name_query = f"SELECT code_name FROM '{table_name}' WHERE code = '{stock_code}' LIMIT 1"
        stock_name = pd.read_sql_query(name_query, conn)['code_name'][0]
        full_name = f"{stock_code} {stock_name}"
        
        #查询日期
        date_condition = ""
        if start is not None:
            date_condition += f" AND date >= '{start}'"  # 添加开始日期条件
        if end is not None:
            date_condition += f" AND date <= '{end}'"  # 添加结束日期条件
        
        # 读取数据到stock_dat
        query = f"""
            SELECT * FROM '{table_name}' 
            WHERE code = '{stock_code}'
            {date_condition}
        """
        stock_dat = pd.read_sql_query(query, conn)
        
        if stock_dat.empty:
            print(f"警告: 未找到 {table_name} 表中代码为 {stock_code} 的数据")
            return stock_dat, full_name
        
        #让x轴显示，需要把索引设为日期
        stock_dat['date'] = pd.to_datetime(stock_dat['date'])
        stock_dat = stock_dat.set_index('date')
        
        return stock_dat, full_name
    
    except Exception as e:
        print(f"数据库操作出错: {str(e)}")
        return pd.DataFrame()
    
    finally:
        # 确保关闭数据库连接
        conn.close()

#-------------------------------------------------------------------------------------
#通过函数接口绘制各类图表
'''
table_name:数据库名，和创建时一样
stock_code：股票名称，sz.或sh.+6位代码
start=None,end=None：开始结束日期，默认数据库里最开始/最后的日期,格式为YYYY-MM-DD
'''

#-------------------------------------------
#绘制k线
def draw_kline_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    layout_dict = {'figsize': (12, 6),
                   'index': stock_dat.index,
                   'draw_kind': {'ochl':
                                     {'open': stock_dat.open,
                                      'close': stock_dat.close,
                                      'high': stock_dat.high,
                                      'low': stock_dat.low
                                      }
                                 },
                   'title': f"{full_name}日k线",
                   'ylabel': "价格"}
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#绘制成交量
def draw_volume_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    bar_red = np.where(stock_dat.open < stock_dat.close,  stock_dat.volume, 0) # 绘制BAR>0 ，上涨
    bar_green = np.where(stock_dat.open > stock_dat.close,  stock_dat.volume, 0) # 绘制BAR<0 下跌

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'bar':
                                     {'bar_red': bar_red,
                                      'bar_green': bar_green
                                      }
                                 },
                   'title': f"{full_name}成交量",
                   'ylabel': "成交量"}
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#绘制均线（20日，30日，60日均线）
def draw_sma_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    #设置常见均线
    stock_dat['SMA20'] = stock_dat['close'].rolling(window=20).mean()
    stock_dat['SMA30'] = stock_dat['close'].rolling(window=30).mean()
    stock_dat['SMA60'] = stock_dat['close'].rolling(window=60).mean()
        
    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'line':
                                     {'SMA20': stock_dat.SMA20,
                                      'SMA30': stock_dat.SMA30,
                                      'SMA60': stock_dat.SMA60
                                      }
                                 },
                   'title': f"{full_name}均线",
                   'ylabel': "价格",
                   'xlabel': "日期",
                   'xticks': 15,
                   'legend': 'best',
                   'xticklabels':'%Y-%m-%d'}
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#绘制KDJ图
def draw_kdj_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)

    #计算RSV
    low_list = stock_dat['low'].rolling(9, min_periods=1).min()
    high_list = stock_dat['high'].rolling(9, min_periods=1).max()
    rsv = (stock_dat['close'] - low_list) / (high_list - low_list) * 100
    
    #计算KDJ
    stock_dat['K'] = rsv.ewm(com=2, adjust=False).mean()
    stock_dat['D'] = stock_dat['K'].ewm(com=2, adjust=False).mean()
    stock_dat['J'] = 3 * stock_dat['K'] - 2 * stock_dat['D']

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'line':
                                     {'K': stock_dat.K,
                                      'D': stock_dat.D,
                                      'J': stock_dat.J
                                      }
                                 },
                   'title': f"{full_name}KDJ",
                   'ylabel': "KDJ",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#绘制MACD图
def draw_macd_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    macd_dif = stock_dat['close'].ewm(span=12, adjust=False).mean() - stock_dat['close'].ewm(span=26, adjust=False).mean()
    macd_dea = macd_dif.ewm(span=9, adjust=False).mean()
    macd_bar = 2 * (macd_dif - macd_dea)

    bar_red = np.where(macd_bar > 0,  macd_bar, 0) # 绘制BAR>0 柱状图
    bar_green = np.where(macd_bar < 0,  macd_bar, 0) # 绘制BAR<0 柱状图

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'bar':
                                     {'bar_red': bar_red,
                                      'bar_green': bar_green
                                      },
                                 'line':
                                     {'macd dif': macd_dif,
                                      'macd dea': macd_dea
                                      }
                                 },
                   'title': f"{full_name}MACD",
                   'ylabel': "MACD",
                   'legend': 'best'}

    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
# 绘制均线金叉和死叉
def draw_cross_annotate(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    # 绘制移动平均线图
    stock_dat['Ma20'] = stock_dat.close.rolling(window=20).mean()  # pd.rolling_mean(stock_dat.Close,window=20)
    stock_dat['Ma30'] = stock_dat.close.rolling(window=30).mean()  # pd.rolling_mean(stock_dat.Close,window=30)

    # 长短期均线序列相减取符号
    list_diff = np.sign(stock_dat['Ma20'] - stock_dat['Ma30'])
    list_signal = np.sign(list_diff - list_diff.shift(1))

    down_cross = stock_dat[list_signal < 0]
    up_cross = stock_dat[list_signal > 0]

    # 循环遍历 显示均线金叉/死叉提示符
    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'line':
                                     {'SMA-20': stock_dat.Ma20,
                                      'SMA-30': stock_dat.Ma30
                                      },
                                 'annotate':
                                     {'死叉':
                                          {'andata': down_cross,
                                           'va':'top',
                                           'xy_y': 'Ma20',
                                           'xytext':(-30,-stock_dat['Ma20'].mean()*0.5),
                                           'fontsize': 8,
                                           'arrow': dict(facecolor='green', shrink=0.1)
                                          },
                                      '金叉':
                                          {'andata': up_cross,
                                           'va': 'bottom',
                                           'xy_y': 'Ma20',
                                           'xytext': (-30, stock_dat['Ma20'].mean() * 0.5),
                                           'fontsize': 8,
                                           'arrow': dict(facecolor='red', shrink=0.1)
                                           }
                                      }
                                 },
                   'title': f"{full_name}均线交叉",
                   'ylabel': "价格",
                   'xlabel': "日期",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#绘制带有跳空缺口的k线图

'''
用于计算跳空能量值
changeRatio:涨/跌幅
preLow, preHigh:昨日高低点
Low, High:今日高低点
threshold:跳空阈值
jump_power:跳空能量
'''
def apply_gap(changeRatio, preLow, preHigh, Low, High, threshold):
    jump_power = 0
    if (changeRatio > 0) and ((Low - preHigh) > threshold):
        # 向上跳空 (今最低-昨最高)/阈值
        jump_power = (Low - preHigh) / threshold # 正数
    elif (changeRatio < 0) and ((preLow - High) > threshold):
        # 向下跳空 (今最高-昨最低)/阈值
        jump_power = (High - preLow) / threshold # 负数
    return jump_power

def draw_gap_annotate(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    jump_threshold = stock_dat.close.median()*0.01 # 跳空阈值 收盘价中位数*0.01
    stock_dat['changeRatio'] = stock_dat.close.pct_change() * 100  # 计算涨/跌幅 (今收-昨收)/昨收*100% 判断向上跳空缺口/向下跳空缺口
    stock_dat['preLow'] = stock_dat.low.shift(1)  # 增加昨日最低价序列
    stock_dat['preHigh'] = stock_dat.high.shift(1) # 增加昨日最高价序列
    stock_dat = stock_dat.assign(jump_power = 0)

    stock_dat['jump_power'] = stock_dat.apply(lambda row:apply_gap(row['changeRatio'],
                                                     row['preLow'],
                                                     row['preHigh'],
                                                     row['low'],
                                                     row['high'],
                                                     jump_threshold),
                                                     axis = 1)
    up_jump = stock_dat[(stock_dat.changeRatio > 0) & (stock_dat.jump_power > 0)]
    down_jump = stock_dat[(stock_dat.changeRatio < 0) & (stock_dat.jump_power < 0)]

    layout_dict = {'figsize': (14, 7),
                   'index': stock_dat.index,
                   'draw_kind': {'ochl':# 绘制K线图
                                     {'open': stock_dat.open,
                                      'close': stock_dat.close,
                                      'high': stock_dat.high,
                                      'low': stock_dat.low
                                      },
                                 'annotate':
                                     {'up':
                                          {'andata': up_jump,
                                           'va': 'top',
                                           'xy_y': 'preHigh',
                                           'xytext': (0,-stock_dat['close'].mean() * 0.5),
                                           'fontsize':  8,
                                           'arrow': dict(facecolor='red', shrink=0.1)
                                           },
                                      'down':
                                          {'andata': down_jump,
                                           'va': 'bottom',
                                           'xy_y': 'preLow',
                                           'xytext': (0,stock_dat['close'].mean() * 0.5),
                                           'fontsize':  8,
                                           'arrow': dict(facecolor='green', shrink=0.1)
                                           }
                                      }
                                 },
                   'title': f"{full_name}-跳空缺口",
                   'ylabel': "价格"}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)

#-------------------------------------------
#周k线绘制
#基于日数据的变换
#也可以使用baostock获取周k月k数据，但是baostock周线每周最后一个交易日才可以获取，月线每月最后一个交易日才可以获取
def draw_kweek_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)

    Freq_T = 'W-FRI'

    #周线Close等于一周中最后一个交易日Close
    week_dat = stock_dat.resample(Freq_T, closed='right', label='right').last()
    #周线Open等于一周中第一个交易日Open
    week_dat.open = stock_dat.open.resample(Freq_T, closed='right', label='right').first()
    #周线High等于一周中High的最大值
    week_dat.high = stock_dat.high.resample(Freq_T, closed='right', label='right').max()
    #周线Low等于一周中Low的最小值
    week_dat.low = stock_dat.low.resample(Freq_T, closed='right', label='right').min()
    #周线Volume等于一周中Volume的总和
    week_dat.volume = stock_dat.volume.resample(Freq_T, closed='right', label='right').sum()

    layout_dict = {'figsize': (14, 7),
                   'index': week_dat.index,
                   'draw_kind': {'ochl':
                                     {'open': week_dat.open,
                                      'close': week_dat.close,
                                      'high': week_dat.high,
                                      'low': week_dat.low
                                      }
                                 },
                   'title': f"{full_name}-周K线",
                   'ylabel': "价格"}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
#支撑线，黄金分割线(加上k线)
def draw_fibonacci_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    #找出此轮走势的最大值和最小值
    Fib_max = stock_dat.close.max()
    #Fib_maxid = stock_dat.index.get_loc(stock_dat.close.idxmax())
    Fib_min = stock_dat.close.min()
    #Fib_minid = stock_dat.index.get_loc(stock_dat.close.idxmin())
    
    Fib_382 = (Fib_max - Fib_min) * 0.382 + Fib_min
    Fib_618 = (Fib_max - Fib_min) * 0.618 + Fib_min

    max_df = stock_dat[stock_dat.close == stock_dat.close.max()]
    min_df = stock_dat[stock_dat.close == stock_dat.close.min()]

    layout_dict = {'figsize': (14, 7),
                   'index': stock_dat.index,
                   'draw_kind': {'ochl':# 绘制K线图
                                     {'open': stock_dat.open,
                                      'close': stock_dat.close,
                                      'high': stock_dat.high,
                                      'low': stock_dat.low
                                      },
                                'hline':
                                    {'Fib_382':
                                         {'pos': Fib_382,
                                          'c': 'r'
                                         },
                                     'Fib_618':
                                         {'pos': Fib_618,
                                          'c': 'g'
                                         }
                                     },
                                 'annotate':
                                     {'max':
                                          {'andata': max_df,
                                           'va': 'top',
                                           'xy_y': 'high',
                                           'xytext': (-30,stock_dat.close.mean()),
                                           'fontsize':  8,
                                           'arrow': dict(facecolor='red', shrink=0.1)
                                           },
                                      'min':
                                          {'andata': min_df,
                                           'va': 'bottom',
                                           'xy_y': 'low',
                                           'xytext': (-30,-stock_dat.close.mean()),
                                           'fontsize':  8,
                                           'arrow': dict(facecolor='green', shrink=0.1)
                                           }
                                      }
                                 },
                   'title': f"{full_name}-黄金分割支撑/阻力位",
                   'ylabel': "价格",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------------------------------------------------
#通过TA-Lib计算的各种技术指标，绘制各类图表

#-------------------------------------------
# 绘制talib SMA移动平均线
def draw_talib_sma_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)

    stock_dat['SMA20'] = talib.SMA(stock_dat.close.values, timeperiod=20)
    stock_dat['SMA30'] = talib.SMA(stock_dat.close.values, timeperiod=30)
    stock_dat['SMA60'] = talib.SMA(stock_dat.close.values, timeperiod=60)
    #stock_dat['SMA20'].fillna(method='bfill',inplace=True)
    #stock_dat['SMA30'].fillna(method='bfill',inplace=True)
    #stock_dat['SMA60'].fillna(method='bfill',inplace=True)


    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'line':
                                     {'SMA20': stock_dat.SMA20,
                                      'SMA30': stock_dat.SMA30,
                                      'SMA60': stock_dat.SMA60
                                      }
                                 },
                   'title': f"{full_name}-SMA-talib",
                   'ylabel': "价格",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)

#-------------------------------------------
# 绘制talib MACD
def draw_talib_macd_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)

    macd_dif, macd_dea, macd_bar = talib.MACD(stock_dat['close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

    macd_dif[np.isnan(macd_dif)] ,macd_dea[np.isnan(macd_dea)], macd_bar[np.isnan(macd_bar)]= 0, 0, 0
    
    bar_red = np.where(macd_bar > 0,  2 * macd_bar, 0)# 绘制BAR>0 柱状图
    bar_green = np.where(macd_bar < 0,  2 * macd_bar, 0)# 绘制BAR<0 柱状图

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'bar':
                                     {'bar_red': bar_red,
                                      'bar_green': bar_green
                                      },
                                 'line':
                                     {'macd dif': macd_dif,
                                      'macd dea': macd_dea
                                      }
                                 },
                   'title': f"{full_name}-MACD-talib",
                   'ylabel': "MACD",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)

#-------------------------------------------
#绘制talib KDJ
def draw_takdj_chart(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)

    stock_dat['K'], stock_dat['D'] = talib.STOCH(stock_dat.high.values, stock_dat.low.values, stock_dat.close.values,
                                           fastk_period=9, slowk_period=3, slowk_matype=MA_Type.SMA, slowd_period=3, slowd_matype=MA_Type.SMA)
    stock_dat['K'].fillna(0,inplace=True), stock_dat['D'].fillna(0,inplace=True)
    stock_dat['J'] = 3 * stock_dat['K'] - 2 * stock_dat['D']

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'line':
                                     {'K': stock_dat.K,
                                      'D': stock_dat.D,
                                      'J': stock_dat.J
                                      }
                                 },
                   'title': f"{full_name}-KDJ-talib",
                   'ylabel': "KDJ",
                   'legend': 'best'}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)
    
#-------------------------------------------
# 绘制 talib K线形态 乌云压顶
#第一日长阳，第二日开盘价高于前一日最高价
def draw_talib_kpattern_annotate(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code,start,end)
    
    CDLDARKCLOUDCOVER = talib.CDLDARKCLOUDCOVER(stock_dat.open.values, stock_dat.high.values, stock_dat.low.values,stock_dat.close.values)

    pattern = stock_dat[(CDLDARKCLOUDCOVER == 100)|(CDLDARKCLOUDCOVER == -100)]

    layout_dict = {'figsize': (14, 7),
                   'index': stock_dat.index,
                   'draw_kind': {'ochl':# 绘制K线图
                                     {'open': stock_dat.open,
                                      'close': stock_dat.close,
                                      'high': stock_dat.high,
                                      'low': stock_dat.low
                                      },
                                 'annotate':
                                     {'CDLDARKCLOUDCOVER':
                                          {'andata': pattern,
                                           'va': 'bottom',
                                           'xy_y': 'high',
                                           'xytext': (0,stock_dat['close'].mean()),
                                           'fontsize': 8,
                                           'arrow': dict(arrowstyle='->',facecolor='blue', connectionstyle="arc3,rad=.2")
                                           }
                                      }
                                 },
                   'title': f"{full_name}-日K线-乌云压顶标注",
                   'ylabel': "价格"}
    
    app=MplVisualIf()
    app.fig_output(**layout_dict)

#-------------------------------------------------------------------------------------
#综合行情分析界面
class MultiGraphIf(MplTypesDraw):
    # 实例化DefTypesPool
    app = DefTypesPool()

    #k线图
    @app.route_types(u"ochl")
    def ochl_graph(self, sub_graph, stock_dat, df_dat=None):
        type_dict = {'Open': stock_dat.open,
                     'Close': stock_dat.close,
                     'High': stock_dat.high,
                     'Low': stock_dat.low
                     }
        view_function = MplTypesDraw.mpl.route_output(u"ochl")
        view_function(stock_dat.index, type_dict, sub_graph)

    @app.route_types(u"sma")
    def sma_graph(self, sub_graph, stock_dat, periods):  # prepare data
        for val in periods:
            type_dict = {'SMA' + str(val): stock_dat.close.rolling(window=val).mean()}
            view_function = MplTypesDraw.mpl.route_output(u"line")
            view_function(stock_dat.index, type_dict, sub_graph)

    @app.route_types(u"vol")
    def vol_graph(self, sub_graph, stock_dat, df_dat=None):  # prepare data
        type_dict = {'bar_red': np.where(stock_dat.open < stock_dat.close, stock_dat.volume, 0),  # 绘制BAR>0 柱状图
                     'bar_green': np.where(stock_dat.open > stock_dat.close, stock_dat.volume, 0)  # 绘制BAR<0 柱状图
                     }
        view_function = MplTypesDraw.mpl.route_output(u"bar")
        view_function(stock_dat.index, type_dict, sub_graph)

    @app.route_types(u"macd")
    def macd_graph(self, sub_graph, stock_dat, df_dat=None):  # prepare data

        macd_dif = stock_dat['close'].ewm(span=12, adjust=False).mean() - stock_dat['close'].ewm(span=26, adjust=False).mean()
        macd_dea = macd_dif.ewm(span=9, adjust=False).mean()
        macd_bar = 2 * (macd_dif - macd_dea)

        type_dict = {'bar_red': np.where(macd_bar > 0, macd_bar, 0),  # 绘制BAR>0 柱状图
                     'bar_green': np.where(macd_bar < 0, macd_bar, 0)  # 绘制BAR<0 柱状图
                     }
        view_function = MplTypesDraw.mpl.route_output(u"bar")
        view_function(stock_dat.index, type_dict, sub_graph)

        type_dict = {'macd dif': macd_dif,
                     'macd dea': macd_dea
                     }
        view_function = MplTypesDraw.mpl.route_output(u"line")
        view_function(stock_dat.index, type_dict, sub_graph)

    @app.route_types(u"kdj")
    def kdj_graph(self, sub_graph, stock_dat, df_dat=None):  # prepare data

        low_list = stock_dat['low'].rolling(9, min_periods=1).min()
        high_list = stock_dat['high'].rolling(9, min_periods=1).max()
        rsv = (stock_dat['close'] - low_list) / (high_list - low_list) * 100
        stock_dat['K'] = rsv.ewm(com=2, adjust=False).mean()
        stock_dat['D'] = stock_dat['K'].ewm(com=2, adjust=False).mean()
        stock_dat['J'] = 3 * stock_dat['K'] - 2 * stock_dat['D']

        type_dict = {'K': stock_dat.K,
                     'D': stock_dat.D,
                     'J': stock_dat.J
                     }
        view_function = MplTypesDraw.mpl.route_output(u"line")
        view_function(stock_dat.index, type_dict, sub_graph)

    def __init__(self, **kwargs):
        MplTypesDraw.__init__(self)
        self.fig = plt.figure(figsize=kwargs['figsize'], dpi=100, facecolor="white")  # 创建fig对象
        self.graph_dict = {}
        self.graph_curr = []

        try:
            gs = gridspec.GridSpec(kwargs['nrows'], kwargs['ncols'],
                                   left=kwargs['left'], bottom=kwargs['bottom'], right=kwargs['right'],
                                   top=kwargs['top'],
                                   wspace=kwargs['wspace'], hspace=kwargs['hspace'],
                                   height_ratios=kwargs['height_ratios'])
        except:
            raise Exception("para error")
        else:
            for i in range(0, kwargs['nrows'], 1):
                self.graph_dict[kwargs['subplots'][i]] = self.fig.add_subplot(gs[i, :])

    def graph_run(self, stock_data, **kwargs):
        # 绘制子图
        self.df_ohlc = stock_data
        for key in kwargs:
            self.graph_curr = self.graph_dict[kwargs[key]['graph_name']]
            for path, val in kwargs[key]['graph_type'].items():
                view_function = MultiGraphIf.app.route_output(path)
                view_function(self.df_ohlc, self.graph_curr, val)
            self.graph_attr(**kwargs[key])
        plt.show()

    def graph_attr(self, **kwargs):

        if 'title' in kwargs.keys():
            self.graph_curr.set_title(kwargs['title'])

        if 'legend' in kwargs.keys():
            self.graph_curr.legend(loc=kwargs['legend'], shadow=True)

        if 'xlabel' in kwargs.keys():
            self.graph_curr.set_xlabel(kwargs['xlabel'])

        self.graph_curr.set_ylabel(kwargs['ylabel'])
        self.graph_curr.set_xlim(0, len(self.df_ohlc.index))  # 设置一下x轴的范围
        self.graph_curr.set_xticks(range(0, len(self.df_ohlc.index), kwargs['xticks']))  # X轴刻度设定 每15天标一个日期

        if 'xticklabels' in kwargs.keys():
            self.graph_curr.set_xticklabels(
                [self.df_ohlc.index.strftime(kwargs['xticklabels'])[index] for index in
                 self.graph_curr.get_xticks()])  # 标签设置为日期

            # X-轴每个ticker标签都向右倾斜45度
            for label in self.graph_curr.xaxis.get_ticklabels():
                label.set_rotation(45)
                label.set_fontsize(10)  # 设置标签字体
        else:
            for label in self.graph_curr.xaxis.get_ticklabels():
                label.set_visible(False)

#-------------------------------------------
def draw_integrated_interface(table_name, stock_code,start=None,end=None):
    stock_dat, full_name = basic_set_plot_stock(table_name, stock_code, start, end)
    layout_dict = {'figsize': (12, 6),
                   'nrows': 4,
                   'ncols': 1,
                   'left': 0.07,
                   'bottom': 0.15,
                   'right': 0.99,
                   'top': 0.96,
                   'wspace': None,
                   'hspace': 0,
                   'height_ratios': [3.5, 1, 1, 1],
                   'subplots': ['kgraph', 'volgraph', 'kdjgraph', 'macdgraph']}

    subplots_dict = {'graph_fst': {'graph_name': 'kgraph',
                                   'graph_type': {'ochl': None,
                                                  'sma': [20, 30, 60, ]
                                                  },
                                   'title': f"{full_name}-日K线",
                                   'ylabel': "价格",
                                   'xticks': 15,
                                   'legend': 'best'
                                   },
                     'graph_sec': {'graph_name': 'volgraph',
                                   'graph_type': {'vol': None
                                                  },
                                   'ylabel': "成交量",
                                   'xticks': 15,
                                   },
                     'graph_thd': {'graph_name': 'kdjgraph',
                                   'graph_type': {'kdj': None
                                                  },
                                   'ylabel': u"KDJ",
                                   'xticks': 15,
                                   'legend': 'best',
                                   },
                     'graph_fth': {'graph_name': 'macdgraph',
                                   'graph_type': {'macd': None
                                                  },
                                   'ylabel': "MACD",
                                   'xlabel': "日期",
                                   'xticks': 15,
                                   'legend': 'best',
                                   'xticklabels': '%Y-%m-%d'  # strftime
                                   },
                     }

    draw_stock = MultiGraphIf(**layout_dict)
    draw_stock.graph_run(stock_dat, **subplots_dict)