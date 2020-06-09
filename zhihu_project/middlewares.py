# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import random
import base64
from scrapy import signals
from zhihu_project.settings import USER_AGENT_LIST, ABUYUN_PASSWORD, ABUYUN_USERNAME
from tools.xici_proxy import XiciProxy
from tools.xila_proxy import XilaProxy


class RandomUserAgentMiddleware(object):
    """ 设置随机的USER-AGENT """
    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(USER_AGENT_LIST)


class RandomFreeProxy(object):
    """ 设置随机的免费代理 """
    def process_request(self, request, spider):
        proxy_list = ['XiciProxy()', 'XilaProxy()']
        while True:
            proxy_object = eval(random.choice(proxy_list))
            result = proxy_object.get_random_ip()
            if bool(result):
                ip, port = result
                request.meta['proxy'] = 'http://{0}:{1}'.format(ip, port)
                break
            else:
                continue


class AbuyunProxy(object):
    """ 设置阿布云的代理 """
    def process_request(self, request, spider):
        request.meta['proxy'] = 'http-dyn.abuyun.com:9020'
        user_password = '{0}:{1}'.format(ABUYUN_USERNAME, ABUYUN_PASSWORD).encode('utf-8')
        b64_user_passwd = base64.b64encode(user_password)
        request.headers['Proxy-Authorization'] = 'Basic ' + b64_user_passwd.decode()


