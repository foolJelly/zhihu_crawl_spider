# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
import pymongo
from pymysql.cursors import DictCursor
from twisted.enterprise import adbapi


class MongoDBPipeline(object):
    """ mongo数据库存储数据 """
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_settings(cls, settings):
        return cls(mongo_uri=settings.get('MONGODB_URI'), mongo_db=settings.get('MONGO_DB'))

    def process_item(self, item, spider):
        if 'ans_id' in item:
            collection = self.db['answer']
            collection.insert_one(dict(item))
        else:
            collection = self.db['question']
            collection.insert_one(dict(item.get_json()))
        return item

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()


class MySQLPipeline(object):
    """ mysql数据库存储数据 """
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    @classmethod
    def from_settings(cls, settings):
        dbparams = dict(
            host=settings.get('MYSQL_HOST'),
            db=settings.get('MYSQL_DBNAME'),
            port=settings.get('MYSQL_PORT'),
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWD')
        )
        conn = pymysql.Connect(**dbparams)
        return cls(conn=conn)

    def process_item(self, item, spider):
        sql_str, item_tuple = item.get_sql()
        self.cursor.execute(sql_str, item_tuple)
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()

