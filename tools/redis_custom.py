import random
from redis import Redis
from zhihu_project.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_SURFACE, REDIS_KEY


class RedisCustom(object):
    """ 自定义redis账号管理池 """

    def __init__(self):
        self.conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    def insert_account(self, account_name, username, password, start_url):
        """ 向redis数据库中添加账号 ，例如: insert_account("account1", "root", "123456", "https://www.baidu.com")"""
        item = dict(username=username, password=password, start_url=start_url)
        account = {account_name: item}
        self.conn.hmset(REDIS_SURFACE, account)
        if self.conn.hexists(REDIS_SURFACE, account_name):
            return '账号成功存入redis数据库'
        else:
            return '账号存入失败'

    def get_account(self):
        """ 随机获取一个账号 """
        keys = self.conn.hkeys(REDIS_SURFACE)
        if bool(keys):
            keys_decode = [item.decode() for item in keys]
            random_account = random.choice(keys_decode)
            account = self.conn.hget(REDIS_SURFACE, random_account)
            account_decode = eval(account.decode())
            if 'cookies' in account_decode:
                return (random_account, account_decode['username'], account_decode['password'], account_decode['start_url'], account_decode['cookies'])
            else:
                return (random_account, account_decode['username'], account_decode['password'], account_decode['start_url'])
        else:
            return 'Redis数据库中没有账号！！！'

    def update_cookies(self, account, username, password, start_url, cookies):
        """ 更新账号的cookie值 """
        item = dict(username=username, password=password, start_url=start_url, cookies=cookies)
        self.conn.hmset(REDIS_SURFACE, {account: item})

    def insert_redis_key(self, star_url):
        """ 向redis数据库中放入起始的url """
        self.conn.lpush(REDIS_KEY, star_url)

if __name__ == "__main__":
    r = RedisCustom()
    r.insert_account('account1', '13100722752', 'qgd13100722752', 'https://www.zhihu.com/api/v3/feed/topstory/recommend?session_token=fe5c619cead22967c73fccb0292eae55&desktop=true&page_number=1&limit=6&action=down&after_id=-1&ad_interval=-1')
    a = r.get_account()
    print(a)