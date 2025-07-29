#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np

#数据库
import sqlite3

#绘图
import matplotlib.pyplot as plt

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
        ohlc = list(zip(np.arange(0,len(df_index)),df_dat['Open'], df_dat['Close'], df_dat['High'], df_dat['Low'])) # 使用zip方法生成数据列表
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