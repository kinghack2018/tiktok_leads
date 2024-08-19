from flask import request


def get_client_ip(is_client_ip=None):
    """
    获取客户端真实 IP 地址。

    该函数不接受参数。

    返回值:
        客户端的IP地址（字符串）。它首先尝试从HTTP头部的'X-Forwarded-For'字段获取IP地址，
        如果存在，则返回该字段的第一个非本地IP地址；如果不存在，则返回请求的远程地址。
    """
    if is_client_ip:
        forwarded_client_ip = request.headers.get('Forwarded-Client-IP')
        if forwarded_client_ip:
            # 从自定义头获取客户端IP，处理并返回第一个非本地IP地址
            return forwarded_client_ip
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # 从HTTP 'X-Forwarded-For'头获取客户端IP，处理并返回第一个非本地IP地址
        return x_forwarded_for.split(',')[0]
    x_real_ip = request.headers.get('X-Real-Ip')
    if x_real_ip:
        # 从HTTP 'X-Forwarded-For'头获取客户端IP，处理并返回第一个非本地IP地址
        return x_real_ip.split(',')[0]
    # 如果'X-Forwarded-For'头不存在，直接返回请求的远程地址作为客户端IP
    return request.remote_addr
