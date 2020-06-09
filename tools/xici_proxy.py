import requests
import random
from lxml import etree
from redis import Redis


class XiciProxy(object):
    """ 西刺代理管理池类 """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.44 Safari/537.36'
        }
        self.conn = Redis(host='127.0.0.1', port=6379, db=1)

    def crawl_ip(self):
        """ 爬取西刺代理 """
        for i in range(1, 6):
            response = requests.get(url='https://www.xicidaili.com/nn/{0}'.format(i), headers=self.headers)
            if response.status_code == 200:
                html = etree.HTML(response.text)
                date_list = html.xpath('//table[@id="ip_list"]/tr')
                for item in date_list[1:]:
                    ip = item.xpath('.//td[2]/text()')[0]
                    port = item.xpath('.//td[3]/text()')[0]
                    publish_time = item.xpath('.//td[last()]/text()')[0]
                    ip_item = {ip: {'ip': ip, 'port': port, 'publish_time': publish_time}}
                    if not bool(self.conn.hexists('xici_proxy', ip)):
                        self.conn.hmset('xici_proxy', ip_item)

    def delete_ip(self, ip):
        """ 删除失效代理 """
        self.conn.hdel('xici_proxy', str(ip))
        if bool(self.conn.hexists('xici_proxy', str(ip))):
            return False
        else:
            return True

    def judge_ip(self, ip, port):
        """ 判断代理是否失效 """
        http_url = 'https://www.zhihu.com/signin?next=%2F'
        proxies = {
            'http': 'http://{0}:{1}'.format(ip, port),
            'https': 'https://{0}:{1}'.format(ip, port),
        }
        try:
            response = requests.get(url=http_url, headers=self.headers, proxies=proxies, timeout=5)
        except:
            print('无效代理：代理名：西刺，IP：{0}， PORT：{1}'.format(ip, port))
            self.delete_ip(ip)
            return False
        else:
            if response.status_code < 200 or response.status_code >= 300:
                self.delete_ip(ip)
                print('无效代理：代理名：西刺，IP：{0}， PORT：{1}'.format(ip, port))
                return False
            else:
                print('有效代理：代理名：西刺，IP：{0}， PORT：{1}'.format(ip, port))
                return True

    def get_random_ip(self):
        """ 获取一个随机代理 """
        if self.conn.exists('xici_proxy'):
            ip_item = self.conn.hkeys('xici_proxy')
            ip_decode = [item.decode() for item in ip_item]
            ip_random = random.choice(ip_decode)
            ip_dict = eval(self.conn.hget('xici_proxy', ip_random).decode())
            ip = ip_dict['ip']
            port = ip_dict['port']
            if self.judge_ip(ip, port):
                return (ip, port)
            else:
                return None
        else:
            self.crawl_ip()


if __name__ == "__main__":
    x = XiciProxy()
    for i in range(474):
        x.get_random_ip()