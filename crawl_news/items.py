# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlNewsItem(scrapy.Item):
    """
        # define the fields for your item here like:
        """
    tbl_tag = scrapy.Field()
    id_picture = scrapy.Field()
    source_title = scrapy.Field()
    source_link = scrapy.Field()
    category_title = scrapy.Field()
    category_link = scrapy.Field()
    post_title = scrapy.Field()
    post_link = scrapy.Field()
    sumary = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    public_date = scrapy.Field()
    update_time = scrapy.Field()
    tag = scrapy.Field()
class ImageItem(scrapy.Item):
    tbl_tag = scrapy.Field()
    id_picture = scrapy.Field()
    image = scrapy.Field()
