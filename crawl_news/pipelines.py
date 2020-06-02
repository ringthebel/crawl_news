import pymysql.cursors
import scrapy
import json
from pymysql import MySQLError
count =0

# connection = pymysql.connect(host='localhost',
#                              user='root',
#                              password='',
#                              db='data_keyphrase',
#                              charset='utf8mb4',
#                              cursorclass=pymysql.cursors.DictCursor)

connection = pymysql.connect(
                            host='139.162.45.23',
                            user='root',
                            password='duydq',
                            db='crawl_tool',
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)

class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = open('output.json', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item

class MyPipeline(object):

    def __init__(self):
        self.items_news = []
        self.items_images = []
        self.count_post = 0
        # self.count_insert = 0
    def process_item(self, item, spider):
        number_post = int(spider.number_post)
        # column = list(item.keys())
        # self.columns = (', '.join(column[1:]))
        # set_values = [item[i] for i in column[1:]]
        
        if item['tbl_tag'] == 'tbl_news':
            column = list(item.keys())
            self.columns = (', '.join(column[1:]))

            set_values = [item[i] for i in column[1:]]
            self.items_news.append(tuple(set_values))
            values = str(self.items_news)[1:-1]
            
            self.count_post += 1
            if len(self.items_news) == 50:
                self.items_news = []
                self.query_new = "INSERT INTO %s (%s) VALUES %s" % ("tbl_news", self.columns, values)
                try:
                    cursor = connection.cursor()  # prepare an object cursor
                    cursor.execute(self.query_new)
                    connection.commit()
                    cursor.close()
                    del cursor
                except MySQLError as ex:
                    connection.rollback()
            if self.count_post == number_post:
                if len(self.items_news) > 0:
                    self.query_new = "INSERT INTO %s (%s) VALUES %s" % ("tbl_news", self.columns, values)
                    try:
                        cursor = connection.cursor()  # prepare an object cursor
                        cursor.execute(self.query_new)
                        connection.commit()
                        cursor.close()
                        del cursor
                        spider.close_down = True
                    except MySQLError as ex:
                        connection.rollback()
                else:
                    spider.close_down = True
        if item['tbl_tag'] == 'tbl_images':
            column = list(item.keys())
            self.columns = (', '.join(column[1:]))

            set_values = [item[i] for i in column[1:]]
            self.items_images.append(tuple(set_values))
            values = str(self.items_images)[1:-1]

            if len(self.items_images) == 50:
                self.items_images = []   
                self.query_image = "INSERT INTO %s (%s) VALUES %s" % ("tbl_images", self.columns, values)
                try:
                    cursor = connection.cursor()  # prepare an object cursor
                    cursor.execute(self.query_image)
                    connection.commit()
                    cursor.close()
                    del cursor
                except MySQLError as ex:
                    connection.rollback()
            
    def close_spider(self, spider):
        print("CLOSE WITHOUT BREAK SYS")