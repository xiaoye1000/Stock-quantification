#用于爬取同花顺网站的股票数据
#数据请求
import requests

#数据解析
import parsel

from ..data_acquisition.stock_get import (
    json_to_str
)

def crawler_ths():
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
