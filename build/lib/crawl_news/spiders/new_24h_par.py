"""
Main scrapy 24h
"""
import sys
import time
import re
import uuid
from scrapy.exceptions import CloseSpider
from datetime import datetime
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem

class HaitugioSpider(scrapy.Spider):
    name = "news_24h"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(HaitugioSpider, self).__init__(*args, **kwargs)
        self.close_down = False

        self.source_title = source_title
        self.source_link = source_link
        self.category_title = category_title
        self.category_link = category_link
        self.number_post = number_post
        if str_detail is not None:
            self.arr_detail = str_detail.split(',')
            
    def start_requests(self):
        """
        start requests
        :return:
        """
        yield scrapy.Request(url=self.category_link, callback=self.next_page)

    def next_page(self, response):
        for i in range(1, 21):
            next_page = response.url + '?vpage=' + str(i)
            yield scrapy.Request(url=next_page, callback=self.get_links)

    def get_links(self, response):
        div_body_above = response.xpath('//div[@class="postx mgbt15"]//article')
        if len(div_body_above) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for _ in div_body_above:
            link = _.xpath('.//a/@href').extract_first()
            title = _.xpath('.//a/@title').extract_first()
            if link.find('vpage') < 0:
                yield scrapy.Request(url=link, callback=self.get_detail_post,
                                    meta={
                                        'post_title': title,
                                        'post_link': link,
                                    })
            else:
                pass
        div_body_down = response.xpath('//div[@class="postx"]//article')
        for _ in div_body_down:
            link = _.xpath('.//a/@href').extract_first()
            title = _.xpath('.//a/@title').extract_first()
            if link.find('vpage') < 0:
                yield scrapy.Request(url=link, callback=self.get_detail_post,
                                    meta={
                                        'post_title': title,
                                        'post_link': link,
                                    })
            else:
                pass

    def get_detail_post(self, response):
        """
        get detail post
        :param response:
        :return:
        """
        if self.close_down:
            raise CloseSpider('OVER NUMBER_POST')

        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
        post_title = response.meta['post_title']
        post_link = response.meta['post_link']
        public_date = response.xpath(
            '//div[@class="updTm updTmD mrT5"]/text()').extract_first()
        if public_date:
            public_date = public_date.strip()
        if public_date:
            date = public_date.split('(')
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', date[0]).strip()
            public_date = datetime.strptime(
                public_date, '%d/%m/%Y %H:%M')
            public_date = public_date.timestamp() * 1000
        tag = ''
        try:
            arr_tag = response.xpath('//a[@class="sbevt clrGr fs12"]/text()').extract()
            for _ in arr_tag:
                tag += _.strip() + '/'
        except:
            pass
        author = response.xpath('//div[@class="nguontin nguontinD bld mrT10 mrB10 fr"]//text()').extract_first()
        if author is not None:
            author = author.strip()
            author = re.sub("\((.*?)\)", "", author)
        if author and len(author) > 50:
            author = ''
        div_body = response.xpath('//article[@class="nwsHt nwsUpgrade"]')
        content = ''
        summary = ''
        if div_body:
            summary = div_body.xpath(
                '//h2[@class="ctTp"]//text()').extract_first()
            div_content = div_body.xpath('.//p')
            if summary is not None:
                summary = summary.strip('\r\n')
                summary = summary.strip()
                if summary[-1] not in ['.', '!', ':', ';', '?']:
                    content = summary + '. '
                else:
                    content = summary + ' '
            else:
                content = ''
            for _ in div_content:
                text = _.xpath('.//text()').extract()
                if text == None or len(text) == 0:
                    continue
                else:
                    if len(text) == 1:
                        if text[0][-1] not in ['.', '!', ':', ';', '?']:
                            content += (text[0].strip() + '. ')
                        else:
                            content += (text[0].strip() + ' ')

                    else:
                        for s in text[:len(text) - 1]:
                            content += s.strip() + ' '
                        try:
                            if text[-1][-1] not in ['.', '!', ':', ';', '?']:
                                content += (text[-1].strip() + '. ')
                            else:
                                content += (text[-1].strip() + ' ')
                        except Exception as e:
                            print(e)
        item = CrawlNewsItem()
        item_image = ImageItem()

        if content is not None and len(content) > 300:
            item['tbl_tag'] = 'tbl_news'
            item['id_picture'] = id_picture
            if 'source_title' in self.arr_detail:
                item['source_title'] = '24h'
            if 'source_link' in self.arr_detail:
                item['source_link'] = 'https://www.24h.com.vn/'
            if 'category_title' in self.arr_detail:
                item['category_title'] = self.category_title
            if 'category_link' in self.arr_detail:
                item['category_link'] = self.category_link
            if 'post_title' in self.arr_detail:
                item['post_title'] = post_title
            if 'post_link' in self.arr_detail:
                item['post_link'] = post_link
            if 'sumary' in self.arr_detail:
                item['sumary'] = summary
            if 'content' in self.arr_detail:
                item['content'] = content
            if 'author' in self.arr_detail:
                item['author'] = author
            if 'update_time' in self.arr_detail:
                item['update_time'] = int(round(time.time() * 1000))
            if 'public_date' in self.arr_detail:
                item['public_date'] = public_date
            if 'tag' in self.arr_detail:
                item['tag'] = tag 
            yield item
            arr_image = div_body.xpath('//p/img[@class="news-image"]/@src').extract()
            arr_image = list(set(arr_image))
            for i in arr_image:
                if i.find('https://cdn.24h.com.vn') == 0:
                    item_image['tbl_tag'] = 'tbl_images'
                    item_image['id_picture'] = id_picture
                    item_image['image'] = i or ''
                    yield item_image

        else:
            print(response.url)