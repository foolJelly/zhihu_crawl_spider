# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ZhihuQuestionItem(scrapy.Item):
    # 问题id
    question_id = scrapy.Field()
    # 问题URL
    question_url = scrapy.Field()
    # 问题
    question = scrapy.Field()
    # 问题描述内容
    question_content = scrapy.Field()
    # 问题标签
    question_tag = scrapy.Field()
    # 关注人数
    follow_num = scrapy.Field()
    # 浏览数
    watch_num = scrapy.Field()
    # 答案总数
    ans_num = scrapy.Field()
    # 爬取时间
    crawl_time = scrapy.Field()

    def clear_data(self):
        """ 清洗item """
        question_id = self['question_id'][0]
        question_url = self['question_url'][0]
        question = self['question'][0]
        question_content = self.setdefault('question_content', '') if not bool(self.setdefault('question_content', '')) else self['question_content'][0]
        question_tag = ';'.join(self['question_tag'])
        follow_num = self['follow_num'][0]
        watch_num = self['watch_num'][0]
        ans_num = self['ans_num'][0]
        crawl_time = self['crawl_time'][0]
        return (question_id, question_url, question, question_content, question_tag, follow_num, watch_num, ans_num, crawl_time)

    def get_json(self):
        """ 将item转换为字典类型 """
        question_id, question_url, question, question_content, question_tag, follow_num, watch_num, ans_num, crawl_time = self.clear_data()
        question_dict = {'question_id': question_id, 'question_url': question_url, 'question': question,
                         'question_content': question_content, 'question_tag': question_tag, 'follow_num': follow_num,
                         'watch_num': watch_num, 'ans_num': ans_num, 'crawl_time': crawl_time}
        return question_dict

    def get_sql(self):
        """ 得到数据库的操作语言以及item """
        sql_str = """insert into zhihu_question(question_id, question_url, question, question_content, question_tag, 
        follow_num, watch_num, ans_num, crawl_time) values (%s, %s, %s, %s, %s, %s, %s, %s, %s) on duplicate key update 
        question_content=values(question_content), question_tag=values(question_tag), follow_num=values(follow_num),
        watch_num=values(watch_num), ans_num=values(ans_num), crawl_time=values(crawl_time)"""
        item = self.clear_data()
        return sql_str, item


class ZhihuAnswerItem(scrapy.Item):
    # 答案id
    ans_id = scrapy.Field()
    # 问题id
    question_id = scrapy.Field()
    # 答案url
    ans_url = scrapy.Field()
    # 作者id
    author_id = scrapy.Field()
    # 答案内容
    content = scrapy.Field()
    # 点赞数
    praise_num = scrapy.Field()
    # 评论数
    comments_num = scrapy.Field()
    # 创建时间
    create_time = scrapy.Field()
    # 答案更新时间
    update_time = scrapy.Field()
    # 爬取时间
    crawl_time = scrapy.Field()

    def get_sql(self):
        """ 得到数据库的操作语言以及item """
        sql_str = """insert into zhihu_answer(ans_id, question_id, ans_url, author_id, content, praise_num, comments_num,
        create_time, update_time, crawl_time) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on duplicate key update 
        content=values(content), praise_num=values(praise_num), comments_num=values(comments_num), update_time=values(update_time),
        crawl_time=values(crawl_time)"""
        item = (self['ans_id'], self['question_id'], self['ans_url'], self['author_id'], self['content'], self['praise_num'],
                self['comments_num'], self['create_time'], self['update_time'], self['crawl_time'])
        return sql_str, item
