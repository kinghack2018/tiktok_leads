import json

import requests
from dateutil.parser import *
from flask import Flask, render_template
from flask_redis import FlaskRedis

from common.ip import get_client_ip
from config.app_config import Config

app = Flask(__name__)
# 从配置对象Config中加载配置信息，以设置应用的运行环境和参数
app.config.from_object(Config)
# 初始化Redis客户端，以便应用可以使用Redis进行数据存储和检索
redis_client = FlaskRedis(app)
# 定义用于存储主播名单信息的键名，以便在Redis中统一管理流媒体数据
leads_key = 'leads'
# 设置主播名单数据在Redis中的过期时间（秒）
leads_ex = 600


def send_authenticated_request(url, cache_key=None, ex=None):
    """
    发送一个经过认证的GET请求。

    参数:
    - url: 请求的URL路径。
    - cache_key: 缓存的键，如果提供，则将响应数据缓存到Redis中。
    - ex: 缓存的过期时间，单位为秒。

    返回值:
    - response: 请求的响应对象。
    """
    # 添加包含认证信息的headers
    headers = {
        'Authorization': f'{app.config["TOKEN"]}',
        'Forwarded-Client-IP': get_client_ip(True)
    }
    # 发送POST请求，并带上认证信息headers
    response = requests.get(app.config['APP_SERVER_URL'] + url, headers=headers)
    # 如果提供了缓存键，则将响应数据缓存到Redis中
    if cache_key is not None:
        # 如果响应状态码为200，表示请求成功
        if response.json().get('code') == 200:
            # 将字典序列化为 JSON 字符串
            json_data = json.dumps(response.json().get('data'))
            # 将JSON字符串设置为Redis缓存
            redis_client.set(cache_key, json_data, ex)
    # 返回响应对象
    return response


@app.route('/')
def get_leads():
    streamer_data = get_streamer()
    # 获取第一条记录
    first_record = streamer_data[0]
    date_obj = parse(first_record.get('user_create_time'))
    # 转换为中文日期时间格式
    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    task_update_time = formatted_date
    for i in range(len(streamer_data)):
        # 将GMT时间字符串转换为datetime对象
        date_obj = parse(streamer_data[i]['user_create_time'])
        # 转换为中文日期时间格式，只显示到小时
        formatted_date = date_obj.strftime('%Y-%m-%d %H:00')
        streamer_data[i]['user_create_time'] = formatted_date

    return render_template('index.html', results=streamer_data, task_update_time=task_update_time)


def get_streamer():
    """
    获取主播名单信息。

    优先从Redis缓存中获取streamer数据，如果缓存命中则解析并返回数据。
    如果缓存未命中，则发送认证请求以获取streamer数据，并将其结果缓存起来。
    """
    # 尝试从Redis缓存中获取streamer数据
    streamer_str = redis_client.get(leads_key)
    if streamer_str is not None:
        # 如果缓存中存在数据，解析并返回
        return json.loads(streamer_str)

    # 发送认证请求并缓存结果
    response = send_authenticated_request('/streamer', leads_key, leads_ex)
    if response.json().get('code') == 200:
        return response.json().get('data')


@app.route('/task_get_streamer')
def task_get_streamer():
    """
    定时获取主播名单任务
    """
    send_authenticated_request('/streamer', leads_key, leads_ex)
    return 'ok\n'


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7000)
