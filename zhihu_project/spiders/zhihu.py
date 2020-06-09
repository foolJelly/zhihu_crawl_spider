# -*- coding: utf-8 -*-
import scrapy
import time
import json
import os
import base64

from html import escape
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from scrapy.loader import ItemLoader
from mouse import move, click

from tools.fateadm_api import FateadmApi
from zheye import zheye
from zhihu_project.settings import CHROMEDRIVER_PATH, COOKIES_PATH, FEIFEI_USERNAME, FEIFEI_PASSWORD, FEIFEI_PD_USER,FEIFEI_PD_PASSWORD
from zhihu_project.items import ZhihuQuestionItem, ZhihuAnswerItem
from tools.redis_custom import RedisCustom
from scrapy_redis.spiders import RedisSpider

# 非分布式则继承scrapy.Spider  例: ZhihuSpider(scrapy.Spider)
class ZhihuSpider(RedisSpider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    # 非分布式运行时注释redis_key，将start_urls的注释取消
    redis_key = 'zhihu:start_urls'
    # start_urls = ['https://www.zhihu.com/api/v3/feed/topstory/recommend?session_token=fe5c619cead22967c73fccb0292eae55&desktop=true&page_number=1&limit=6&action=down&after_id=-1&ad_interval=-1']

    # 知乎答案的api
    ans_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=5&offset={1}&platform=desktop&sort_by=default"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
    }

    # 运行401的状态码通过，返回401说明cookie值失效
    custom_settings = {
        "HTTPERROR_ALLOWED_CODES": [401]
    }

    # 自定义的账号管理池类
    redis = RedisCustom()
    account_item = redis.get_account()

    # 初始化状态码
    statu_code = 200

    # def start_requests(self):
    #     """ 非分布式爬虫测试时的spider的入口方法，非分布式时取消注释 """
    #     yield self.selenuim_parse(url=self.start_urls[0])

    def make_requests_from_url(self, url):
        """ 分布式爬虫的spider入口方法 """
        return self.selenuim_parse(url=url)

    def selenuim_parse(self, url):
        """ 使用selenium模拟登录知乎网站 """
        # 若用文件保存cookie则取消一下注释，并注释if self.statu_code == 401 or len(self.account_item) < 5:
        # 使用文件保持则无法使用自定义账号管理池类，需将相关内容注释，即与self.account_item相关内容
        # if not bool(os.path.exists(COOKIES_PATH+'/cookies.json')):
        #     with open(COOKIES_PATH + '/cookies.json', 'w') as f:
        #         pass
        # with open(COOKIES_PATH+'/cookies.json', 'r') as f:
        #     try:
        #         cookie = json.load(f)
        #     except:
        #         cookie = None
        # if not bool(cookie):
        if self.statu_code == 401 or len(self.account_item) < 5:
            options = Options()
            options.add_argument('--disable-extensions')
            # 将调试selenium的端口设置为9222
            options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
            browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
            try:
                browser.maximize_window()
            except:
                pass

            browser.get("https://www.zhihu.com/signin?next=%2F")

            browser.find_element_by_xpath('//div[not(contains(text(),"免")) and contains(text(),"密码")]').click()
            browser.find_element_by_xpath('//input[contains(@placeholder,"手机号或邮箱")]').send_keys(Keys.CONTROL + "a")
            browser.find_element_by_xpath('//input[contains(@placeholder,"手机号或邮箱")]').send_keys(self.account_item[1])
            browser.find_element_by_xpath('//input[contains(@placeholder,"密码")]').send_keys(Keys.CONTROL + "a")
            browser.find_element_by_xpath('//input[contains(@placeholder,"密码")]').send_keys(self.account_item[2])
            browser.find_element_by_xpath('//button[@type="submit"]').click()

            time.sleep(3)
            login_flag = False
            while not login_flag:
                try:
                    browser.find_element_by_xpath('//button[contains(text(),"提问")]')
                    cookies = browser.get_cookies()
                    cookies_file = {item['name']: item['value'] for item in cookies}
                    self.redis.update_cookies(self.account_item[0], self.account_item[1], self.account_item[2],
                                              self.account_item[3], cookies_file)
                    # with open(COOKIES_PATH+'/cookies.json', 'w') as f:
                    #     f.write(json.dumps(cookies_file, ensure_ascii=False))
                    browser.close()
                    login_flag = True
                    return scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                         cookies=cookies_file)
                except:
                    pass

                try:
                    eng_yzm = browser.find_element_by_xpath('//img[@class="Captcha-englishImg"]')
                except:
                    eng_yzm = None

                try:
                    chn_yzm = browser.find_element_by_xpath('//img[@class="Captcha-chineseImg"]')
                except:
                    chn_yzm = None

                if bool(eng_yzm):
                    # 使用菲菲打码平台解析英文数字的验证码
                    img_yzm_str = eng_yzm.get_attribute('src')
                    img_yzm = img_yzm_str.replace('data:image/jpg;base64,', '').replace("%0A", "")
                    with open('eng_yzm.jpeg', 'wb') as img_file:
                        img_file.write(base64.b64decode(img_yzm))
                    feifei = FateadmApi(FEIFEI_USERNAME, FEIFEI_PASSWORD, FEIFEI_PD_USER, FEIFEI_PD_PASSWORD)
                    code = feifei.PredictFromFileExtend("30400", "eng_yzm.jpeg")
                    browser.find_element_by_xpath('//input[@placeholder="验证码"]').send_keys(code)
                    time.sleep(1)
                    browser.find_element_by_xpath('//button[@type="submit"]').click()
                    time.sleep(3)

                if bool(chn_yzm):
                    # 使用zheye模块识别倒立汉字验证码
                    img_yzm_str = chn_yzm.get_attribute('src')
                    img_yzm = img_yzm_str.replace('data:image/jpg;base64,', '').replace("%0A", "")
                    with open('chn_yzm.jpeg', 'wb') as img_file:
                        img_file.write(base64.b64decode(img_yzm))
                    img_location = chn_yzm.location
                    # 获取浏览器工具栏的高度
                    browser_height = browser.execute_script('return window.outerHeight - window.innerHeight;')
                    z = zheye()
                    # zheye模块识别后返回一个装有二元组的列表，形如：[(y,x)]
                    hz = z.Recognize('chn_yzm.jpeg')
                    if len(hz) == 2:
                        x1 = int(hz[0][1]) // 2 + img_location['x']
                        y1 = int(hz[0][0]) // 2 + img_location['y'] + browser_height
                        move(x1, y1)
                        click()
                        time.sleep(3)
                        x2 = int(hz[1][1]) // 2 + img_location['x']
                        y2 = int(hz[1][0]) // 2 + img_location['y'] + browser_height
                        move(x2, y2)
                        click()
                    else:
                        x1 = int(hz[0][1]) // 2 + img_location['x']
                        y1 = int(hz[0][0]) // 2 + img_location['y'] + browser_height
                        move(x1, y1)
                        click()
                    time.sleep(1)
                    browser.find_element_by_xpath('//button[@type="submit"]').click()
                    time.sleep(3)
        else:
            return scrapy.Request(url=url, callback=self.parse, headers=self.headers,
                                 cookies=self.account_item[4])

    def parse(self, response):
        """ 解析登陆后的内容页推荐频道的api获取问题的id """
        # 若cookie值失效，则重新模拟登录
        if response.status == 401:
            self.statu_code = 401
            yield self.selenuim_parse()
        json_text = json.loads(response.text)
        is_end = json_text['paging']['is_end']
        next_page = json_text['paging']['next']
        data_list = json_text['data']
        for item in data_list:
            question = item.get('target').get('question', None)
            if bool(question):
                question_id = question['id']
                question_url = 'https://www.zhihu.com/question/' + str(question_id)
                yield scrapy.Request(url=question_url, callback=self.parse_question, headers=self.headers, meta={'question_id': question_id})
            else:
                continue
        if not is_end:
            yield scrapy.Request(url=next_page, callback=self.parse)
        else:
            # 推荐频道的所有问题id提取完后，向redis中重新插入起始的url，这样又可以获取新的推荐内容的问题id
            self.redis.insert_redis_key(self.account_item[3])

    def parse_question(self, response):
        """ 解析问题页面的详情信息，该页面提取的信息是静态的数据，可直接用xpath提取 """
        question_id = response.meta.get('question_id')
        item_content = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_content.add_value('question_id', question_id)
        item_content.add_value('question_url', response.url)
        item_content.add_xpath('question', '//div[@class="QuestionHeader"]//h1[@class="QuestionHeader-title"]/text()')
        item_content.add_xpath('question_content', '//div[@class="QuestionHeader"]//span[contains(@class,"RichText")]/text()')
        item_content.add_xpath('question_tag', '//div[@class="QuestionHeader"]//div[contains(@class,"Tag")]//div[@class="Popover"]/div/text()')
        item_content.add_xpath('follow_num', '//div[@class="QuestionHeader-side"]//div[contains(text(),"关注者")]/following-sibling::strong/text()')
        item_content.add_xpath('watch_num', '//div[@class="QuestionHeader-side"]//div[contains(text(),"被浏览")]/following-sibling::strong/text()')
        item_content.add_xpath('ans_num', '//div[@class="Question-mainColumn"]/div[1]/a[contains(text(),"查看全部")]/text() | //h4[@class="List-headerText"]/span/text()[1]')
        item_content.add_value('crawl_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        yield scrapy.Request(url=self.ans_url.format(question_id, 0), callback=self.parse_answer, headers=self.headers, meta={'question_id': question_id, 'question_url': response.url})

        yield item_content.load_item()

    def parse_answer(self, response):
        """ 解析答案的相关信息,答案相关信息是在问题动态加载的,可找到相关api进行提取 """
        question_id = response.meta.get('question_id')
        question_url = response.meta.get('question_url')
        json_text = json.loads(response.text)
        is_end = json_text['paging']['is_end']
        next_page = json_text['paging']['next']
        data_list = json_text['data']
        for item in data_list:
            ans_content = ZhihuAnswerItem()
            ans_content['ans_id'] = item['id']
            ans_content['question_id'] = question_id
            ans_content['ans_url'] = question_url + '/answer/'+str(item['id'])
            ans_content['author_id'] = item['author']['id'] if 'id' in item['author'] else None
            ans_content['content'] = escape(item['content'])
            ans_content['praise_num'] = item['voteup_count']
            ans_content['comments_num'] = item['comment_count']
            ans_content['create_time'] = datetime.fromtimestamp(int(item['created_time'])).strftime('%Y-%m-%d %H:%M:%S')
            ans_content['update_time'] = datetime.fromtimestamp(int(item['updated_time'])).strftime('%Y-%m-%d %H:%M:%S')
            ans_content['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            yield ans_content

        if not is_end:
            yield scrapy.Request(url=next_page, callback=self.parse_answer, headers=self.headers, meta={'question_id': question_id, 'question_url': question_url})

