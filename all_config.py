#用于配置所有个人数据
#1.tushare个人API接口
#2.爬虫个人请求头、cookies
import json
import os
import tushare as ts

#-----------------------------------------------------------------------
#验证Tushare API密钥是否有效
def validate_tushare_api(api_key):
    try:
        # 初始化Tushare Pro接口
        pro = ts.pro_api(api_key)

        # 尝试调用一个简单的接口来验证API
        df = pro.tmt_twincome(item='8', start_date='20180101', end_date='20180201')

        # 如果成功获取数据且不为空，则API有效
        if df is not None and not df.empty:
            print("API验证成功！")
            return True
        else:
            print("API验证失败：返回数据为空")
            return False

    except Exception as e:
        print(f"API验证失败：{str(e)}")
        return False

def tushare_apiget():
    tushare_api = input("配置个人数据，请输入tushare的API（不需要则输入None）：").strip()

    if tushare_api is None:
        return None
    else:
        val = validate_tushare_api(tushare_api)
        if val:
            return tushare_api
        else:
            return None

#-----------------------------------------------------------------------
def headers_cookies_get():
    headers_input = input("请输入请求头（不需要则输入None）:").strip()
    cookies_input = input("请输入cookies（不需要则输入None）").strip()

    headers_dict = None if headers_input.lower() == "none" else {}
    cookies_dict = None if cookies_input.lower() == "none" else {}

    # 处理请求头
    if headers_dict is not None and headers_input:
        if ':' in headers_input:
            # 多行键值对格式
            for line in headers_input.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers_dict[key.strip()] = value.strip()
        else:
            # 单行User-Agent格式
            headers_dict['User-Agent'] = headers_input

    # 处理Cookies
    if cookies_dict is not None and cookies_input:
        if '=' in cookies_input:
            # 标准Cookie格式：key1=value1; key2=value2
            for item in cookies_input.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies_dict[key.strip()] = value.strip()
        else:
            # 单值Cookie格式
            cookies_dict['cookie'] = cookies_input

    return headers_dict, cookies_dict

# -----------------------------------------------------------------------
# 保存配置到文件
def save_config_to_file(config_data):
    # 确保config目录存在
    config_dir = "stock_project/data/config"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # 保存配置到文件
    filepath = os.path.join(config_dir, "config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

    print(f"配置已保存到: {filepath}")

#-----------------------------------------------------------------------
#主函数
def config_data_get():
    tushare_api = tushare_apiget()
    headers, cookies=headers_cookies_get()

    # 创建配置字典
    config_data = {
        "tushare_api": tushare_api,
        "headers": headers,
        "cookies": cookies
    }

    # 保存配置到文件
    save_config_to_file(config_data)

    return None


