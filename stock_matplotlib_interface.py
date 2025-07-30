#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

#数据库
import sqlite3

#绘图
import matplotlib.pyplot as plt

#k线
import mpl_finance as mpf

#将各种不同类型的图表函数注册到该容器中，方便调用
class Def_Types_Pool():
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
        #print(u"output [%s] function:" % path)
        function_val = self.routes.get(path)
        if function_val:
            return function_val
        else:
            raise ValueError('Route "{}"" has not been registered'.format(path))

#实现各种类型的指标函数绘制
class Mpl_Types_Draw():
    
    '''
    df_index: 时间序列索引
    df_dat: 数据
    graph: matplotlib的axes对象
    '''

    #实例化Def_Types_Pool
    mpl = Def_Types_Pool()

    #-------------------------------------------
    #使用装饰器，注册到self.routes中
    #折线图
    @mpl.route_types(u"line")
    def line_plot(df_index, df_dat, graph):
        # 绘制line图
        for key, val in df_dat.items():
            graph.plot(np.arange(0, len(val)), val, label=key, lw=1.0)
    
    #-------------------------------------------
    # 绘制ochl图(k线)
    @mpl.route_types(u"ochl")
    def ochl_plot(df_index, df_dat, graph):
        # 方案一
        #mpf.candlestick2_ochl(graph, df_dat['open'], df_dat['close'], df_dat['high'], df_dat['low'], width=0.5,
        #                      colorup='r', colordown='g') # 绘制K线走势
        # 方案二
        ohlc = list(zip(np.arange(0,len(df_index)),df_dat['open'], df_dat['close'], df_dat['high'], df_dat['low'])) # 使用zip方法生成数据列表
        mpf.candlestick_ochl(graph, ohlc, width=0.2, colorup='r', colordown='g', alpha=1.0) # 绘制K线走势
    
    #-------------------------------------------
    #柱状图（成交量）
    @mpl.route_types(u"bar")
    def bar_plot(df_index, df_dat, graph):
        #graph.bar(np.arange(0, len(df_index)), df_dat['Volume'], \
        #         color=['g' if df_dat['Open'][x] > df_dat['Close'][x] else 'r' for x in range(0,len(df_index))])

        graph.bar(np.arange(0, len(df_index)), df_dat['bar_red'], facecolor='red')
        graph.bar(np.arange(0, len(df_index)), df_dat['bar_green'], facecolor='green')
        
    #-------------------------------------------
    # 移动平均线（均线）
    @mpl.route_types(u"hline")
    def hline_plot(df_index, df_dat, graph):
        #子图上绘制
        for key, val in df_dat.items():
            graph.axhline(val['pos'], c=val['c'], label=key)
     
    #-------------------------------------------
    #金叉/死叉标注点
    @mpl.route_types(u"annotate")
    def annotate_plot(df_index, df_dat, graph):
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
    def hline_plot(df_index, df_dat, graph):
        for key, val in df_dat.items():
            graph.axhline(val['pos'], c=val['c'], label=key)

#绘制完整的图表
class Mpl_Visual_If(Mpl_Types_Draw): 

    #构造函数
    def __init__(self):
        Mpl_Types_Draw.__init__(self)

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
            self.graph.set_xticklabels([self.index.strftime(kwargs['xticklabels'])[index]                                         for index in self.graph.get_xticks()])
        else:
            self.graph.set_xticklabels([self.index.strftime('%Y-%m-%d')[index]                                         for index in self.graph.get_xticks()])
            
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
def basic_set_plot_stock(table_name, stock_code):
    # 基础配置
    plt.rcParams['font.sans-serif'] = ['SimHei'] 
    plt.rcParams['axes.unicode_minus'] = False
    
    #注意需要先生成数据库
    #连接/创建数据库
    conn = sqlite3.connect('stock-data.db')
    
    try:
        # 读取数据
        query = f"SELECT * FROM '{table_name}' WHERE code = '{stock_code}'"
        stock_dat = pd.read_sql_query(query, conn)
        
        if stock_dat.empty:
            print(f"警告: 未找到 {table_name} 表中代码为 {code} 的数据")
            return stock_dat
        
        #让x轴显示，需要把索引设为日期
        stock_dat['date'] = pd.to_datetime(stock_dat['date'])
        stock_dat = stock_dat.set_index('date')
        
        return stock_dat
    
    except Exception as e:
        print(f"数据库操作出错: {str(e)}")
        return pd.DataFrame()
    
    finally:
        # 确保关闭数据库连接
        conn.close()

#-------------------------------------------------------------------------------------
#通过接口绘制各类图表的函数
def draw_kline_chart(table_name, stock_code):
    stock_dat=basic_set_plot_stock(table_name, stock_code)
    layout_dict = {'figsize': (12, 6),
                   'index': stock_dat.index,
                   'draw_kind': {'ochl':
                                     {'open': stock_dat.open,
                                      'close': stock_dat.close,
                                      'high': stock_dat.high,
                                      'low': stock_dat.low
                                      }
                                 },
                   'title': "002625光启技术日k线",
                   'ylabel': "价格"}
    app=Mpl_Visual_If()
    app.fig_output(**layout_dict)

#-------------------------------------------
#绘制成交量
def draw_volume_chart(table_name, stock_code):
    stock_dat=basic_set_plot_stock(table_name, stock_code)
    bar_red = np.where(stock_dat.open < stock_dat.close,  stock_dat.volume, 0) # 绘制BAR>0 ，上涨
    bar_green = np.where(stock_dat.open > stock_dat.close,  stock_dat.volume, 0) # 绘制BAR<0 下跌

    layout_dict = {'figsize': (14, 5),
                   'index': stock_dat.index,
                   'draw_kind': {'bar':
                                     {'bar_red': bar_red,
                                      'bar_green': bar_green
                                      }
                                 },
                   'title': "002625光启技术-成交量",
                   'ylabel': "成交量"}
    app=Mpl_Visual_If()
    app.fig_output(**layout_dict)
#-------------------------------------------
#绘制均线（20日，30日，60日均线）
def draw_sma_chart(table_name, stock_code):
    stock_dat=basic_set_plot_stock(table_name, stock_code)
    
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
                   'title': "002625光启技术-均线",
                   'ylabel': "价格",
                   'xlabel': "日期",
                   'xticks': 15,
                   'legend': 'best',
                   'xticklabels':'%Y-%m-%d'}
    app=Mpl_Visual_If()
    app.fig_output(**layout_dict)
    
    
#-------------------------------------------
#绘制KDJ图
def draw_kdj_chart(table_name, stock_code):
    stock_dat=basic_set_plot_stock(table_name, stock_code)

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
                   'title': "002625光启技术-KDJ",
                   'ylabel': "KDJ",
                   'legend': 'best'}
    
    app=Mpl_Visual_If()
    app.fig_output(**layout_dict)