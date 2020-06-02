"""
Main scrapy 24h
"""
import json
import sys
import time
import re
import uuid
from datetime import datetime
from scrapy.exceptions import CloseSpider
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem

class DanTriSpider(scrapy.Spider):

    name = "news_dantri"
    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(DanTriSpider, self).__init__(*args, **kwargs)
        self.close_down = False
        self.category_link = category_link
        self.source_title = source_title
        self.source_link = source_link
        self.category_title = category_title
        self.number_post = number_post
        self.str_detail = str_detail
        if str_detail != None:
            self.arr_detail = self.str_detail.split(',')

    def start_requests(self):
        """
        start requests
        :return:
        """
        yield scrapy.Request(url=self.category_link, callback=self.get_links)
    def get_links(self, response):
        """
                get link posts in category
                :param response:
                :return:
                """

        div_body = response.xpath('//div[@class="fl wid470"]')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        div_posts = div_body.xpath('.//div[@class="mr1"]/h2')
        if div_posts:
            for div in div_posts:
                link = div.xpath('./a/@href').extract_first()
                title = div.xpath('./a/@title').extract_first()

                if title:
                    if link.find("http") < 0:
                        link = "https://dantri.com.vn" + link
                        print("link post", link)
                        yield scrapy.Request(url=link, callback=self.get_detail_post,
                                             meta={
                                                 'post_title': title,
                                                 'post_link': link,
                                             })

        next_page = response.xpath('//div[@class="clearfix mt1"]/div[@class="fr"]/a[@class="fon27 mt1 mr2"]/@href').get()
        if next_page is not None:
            url_nextpage = "https://dantri.com.vn" + next_page
            yield scrapy.Request(url=url_nextpage, callback=self.get_links)

    def get_detail_post(self, response):
        """
        get detail post
        :param response:
        :return:
        """
        if self.close_down:
            raise CloseSpider('OVER NUMBER_POST')
        post_title = response.meta['post_title']
        post_link = response.meta['post_link']
        content = ''
        summary = ''
        author = ''
        public_date = response.xpath(
            '//span[@class="fr fon7 mr2 tt-capitalize"]/text()').extract_first()
        try:
            if public_date:
                public_date = public_date.strip()
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', public_date).strip()
            public_date = datetime.strptime(
                public_date, '%d/%m/%Y - %H:%M')
            public_date = public_date.timestamp() * 1000
        except Exception as e:
            print(e)
        arr_summary = response.xpath('//h2[@class="fon33 mt1 sapo"]//text()').extract()
        if len(arr_summary) > 3:
            for s in arr_summary[2:]:
                s = s.strip('\r\n')
                s = s.strip()
                content +=s
            if content[-1] not in ['.', '!', ':', ';', '?']:
                content = content + '. '
                summary = content
            else:
                content = content + ' '
                summary = content
        else:
            pass
        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
        tag = ''
        try:
            div_tag = response.xpath('//span[@class="news-tags-item"]/a')
            for _ in div_tag:
                str_tag = _.xpath('//text()').extract_first()
                tag = str_tag.strip() + '/'
        except:
            pass
        div_body = response.xpath('//div[@class="fon34 mt3 mr2 fon43 detail-content"]')

        if div_body:
            div_content = div_body.xpath('.//p')
            author = div_content[-1].xpath('.//text()').extract_first()
            if author is not None:
                author = author.strip()
                author = re.sub("\((.*?)\)", "", author)
            if author and len(author) > 50:
                author = ''
            for _ in div_content[:len(div_content)-1]:
                text = _.xpath('.//text()').extract()
                if text == None or len(text) == 0 or text == ['\r\n']:
                    continue
                else:
                    if '\r\n' in text:
                        text.remove('\r\n')
                    else:
                        pass
                    if len(text) == 1:

                        text = text[0].strip()
                        if text != '':
                            if text[-1] not in ['.', '!', ':', ';', '?']:
                                content += (text + '. ')
                            else:
                                content += (text + ' ')

                    else:

                        for s in text[:len(text) - 1]:
                            content += s.strip() + ' '
                        try:
                            text = text[-1].strip()
                            if text != '':
                                if text[-1] not in ['.', '!', ':', ';', '?']:
                                    content += (text + '. ')
                                else:
                                    content += (text + ' ')
                        except Exception as e:
                            print(e)
            if len(content) < 500:
                if len(div_body.xpath('.//figure').extract()) >12:
                    pass
                else:
                    div_content = div_body.xpath('./div')
                    try:
                        author = div_content[-1].xpath('.//text()').extract_first()
                        if author is not None:
                            author = author.strip()
                            author = re.sub("\((.*?)\)", "", author)
                        if author and len(author) > 50:
                            author = ''
                        for _ in div_content[:len(div_content) - 1]:
                            text = _.xpath('.//text()').extract()
                            if text == None or len(text) == 0 or text == ['\r\n']:
                                continue
                            else:
                                if '\r\n' in text:
                                    text.remove('\r\n')
                                else:
                                    pass
                                if len(text) == 1:

                                    text = text[0].strip()
                                    if text != '':
                                        if text[-1] not in ['.', '!', ':', ';', '?']:
                                            content += (text + '. ')
                                        else:
                                            content += (text + ' ')

                                else:

                                    for s in text[:len(text) - 1]:
                                        content += s.strip() + ' '
                                    try:
                                        text = text[-1].strip()
                                        if text != '':
                                            if text[-1] not in ['.', '!', ':', ';', '?']:
                                                content += (text + '. ')
                                            else:
                                                content += (text + ' ')
                                    except Exception as e:
                                        print(e)
                    except Exception as e:
                        print(e)
        item = CrawlNewsItem()
        item_image = ImageItem()

        item['tbl_tag'] = 'tbl_news'
        item['id_picture'] = id_picture
        if 'source_title' in self.arr_detail:
            item['source_title'] = 'dantri'
        if 'source_link' in self.arr_detail:
            item['source_link'] = 'https://dantri.com.vn/'
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

        arr_image = div_body.xpath('//figure//img/@src').extract()
        arr_image = list(set(arr_image))
        for i in arr_image:
            if i.find('https://icdn.dantri.com.vn') == 0:
                item_image['tbl_tag'] = 'tbl_images'
                item_image['id_picture'] = id_picture
                item_image['image'] = i
                yield item_image
