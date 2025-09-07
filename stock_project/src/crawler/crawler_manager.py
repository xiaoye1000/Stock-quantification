#用于爬取同花顺网站的股票数据
#数据请求
import requests

#数据解析
import parsel

from ..data_acquisition.stock_get import (
    json_to_str
)

'''
可以获取config中的预设请求头和cookies，也可以在函数输入时输入cookies
'''

#获取配置数据
def get_headers_cookies():
    #配置数据
    config_data = json_to_str()
    if not config_data:
        print("无法获取配置数据，请检查config.json文件")
        return None

    # 请求头
    headers = config_data.get("headers", "")
    #print(headers)

    #cookies
    cookies = config_data.get("cookies", "")
    #print(cookies)
    return headers, cookies

#同花顺网站爬取
def crawler_ths(cookies_get = None):
    if cookies_get is None:
        headers, cookies = get_headers_cookies()
    else:
        headers, cookies = get_headers_cookies()
        cookies = cookies_get

    # 链接(同花顺）
    for page in range(1,272):
        print(f'正在采集第{page}页的数据')
        url = f'https://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/{page}/ajax/1/'

        # 发送请求
        response = requests.get(url=url, headers=headers, cookies=cookies)

        # 获取数据
        html_data = response.text

        # 转换数据
        selector = parsel.Selector(html_data)
        trs = selector.css('.m-table tr')[1:]
        for tr in trs:
            # 数据具体内容
            info_1 = tr.css('td a::text').getall()  # 代码、名称
            info_2 = tr.css('td::text').getall()  # 除代码名称的其他数据

            print(info_1)
            print(info_2)

            # 数据存入到字典
            dit = {
                '代码': info_1[0],
                '名称': info_1[1],
                '现价': info_2[1],
                '涨跌幅': info_2[2],
                '涨跌': info_2[3],
                '涨速': info_2[4],
                '换手': info_2[5],
                '量比': info_2[6],
                '振幅': info_2[7],
                '成交额': info_2[8],
                '流通股': info_2[9],
                '流通市值': info_2[10],
                '市盈率': info_2[11],
            }

            # 存入代码占位

            print(dit)
    return None


#雪球网站爬取
def crawler_xq(cookies_get = None):
    if cookies_get is None:
        headers, cookies = get_headers_cookies()
    else:
        headers, cookies = get_headers_cookies()
        cookies = cookies_get

    for page in range(1, 167):

        url = f'https://stock.xueqiu.com/v5/stock/screener/quote/list.json?page={page}&size=30&order=desc&order_by=percent&market=CN&type=sh_s'

        # 发送请求
        response = requests.get(url=url, headers=headers, cookies=cookies)

        json_data = response.json()
        for index in json_data['data']['list']:
            #print(index)
            dit = {
                '代码':index['symbol'],
                '名称':index['name'],
                '现价':index['current'],
                '涨跌幅':index['percent'],
                '涨跌':index['chg'],
                '年初至今':index['current_year_percent'],
                '成交量':index['volume'],
                '成交额':index['amount'],
                '换手率':index['turnover_rate'],
                '市盈率':index['pe_ttm'],
                '股息率':index['dividend_yield'],
                '市值':index['market_capital']
            }

            #存入代码占位

            print(dit)
    return None


