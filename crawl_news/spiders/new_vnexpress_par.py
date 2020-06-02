from datetime import datetime
import time
import scrapy
import uuid
import json
import pickle
import re
from ..items import ImageItem
from ..items import CrawlNewsItem
from scrapy.exceptions import CloseSpider

class VnExpressSpider(scrapy.Spider):
    """
    Main scrapy vnexpress
    """
    name = "news_vnexpress"
    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None, number_post=None,
                 str_detail=None, *args, **kwargs):
        super(VnExpressSpider, self).__init__(*args, **kwargs)
        self.close_down = False
        self.source_title = source_title
        self.source_link = source_link
        self.category_title = category_title
        self.category_link = category_link
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
        category = []

        div_body = response.xpath('//section[@class="container"]//article[@class="list_news"]')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for div in div_body:
            link = div.xpath('.//a/@href').extract_first()
            title = div.xpath('.//a/text()').extract_first()
            if link:
                link = 'https://vnexpress.net' + link
                category.append((title, link))
        for _ in category:
            yield scrapy.Request(url=_[1], callback=self.get_detail_post,
                                 meta={
                                     'post_title': _[0],
                                     'post_link': _[1]
                                 })

        arr_next_page = response.xpath(
            '//div[@class="pagination mb10"]/a/@href').extract()
        if arr_next_page[-1] is not None:
            if arr_next_page[-1].find("http") < 0:
                next_page = 'https://vnexpress.net' + arr_next_page[-1]
            else:
                next_page = arr_next_page[-1]
            yield scrapy.Request(url=next_page, callback=self.get_links)

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
        date = response.xpath(
            '//header[@class="clearfix"]//span/text()').extract()
        if len(date) > 1:
            public_date = date[0] + ' ' + date[2]
        else:
            public_date = date[0]
        if public_date:
            public_date = public_date.strip()
            date = public_date.split('(')
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', date[0]).strip()
            public_date = datetime.strptime(
                public_date, '%d/%m/%Y %H:%M')
            public_date = public_date.timestamp() * 1000
            content = ''
            title = response.xpath('//section[@class="sidebar_1"]//h1//text()').extract_first()
            if title is not None:
                title = title.strip('\r\n')
                title = title.strip()
                if title[-1] not in ['.', '!', ':', ';', '?']:
                    content = title + '. '
                else:
                    content = title + ' '
            else:
                content = ''

            summary = response.xpath('//section[@class="sidebar_1"]//p[@class="description"]//text()').extract_first()
            if summary is not None:
                summary = summary.strip('\r\n')
                summary = summary.strip()
                if summary[-1] != '.' and (summary[-1] not in ['!', ':', ';', '?']):
                    content = summary + '. '
                else:
                    content = summary + ' '
            else:
                content = ''
            div_body = response.xpath('//article[@class="content_detail fck_detail width_common block_ads_connect"]')

            if div_body:
                div_content = div_body.xpath('.//p')
                for _ in div_content:
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

                id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
                item = CrawlNewsItem()
                item_image = ImageItem()

                item['tbl_tag'] = 'tbl_news'
                item['id_picture'] = id_picture
                if 'source_title' in self.arr_detail:
                    item['source_title'] = 'vnexpress'
                if 'source_link' in self.arr_detail:
                    item['source_link'] = 'https://vnexpress.net/'
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
                    item['author'] = ''
                if 'update_time' in self.arr_detail:
                    item['update_time'] = int(round(time.time() * 1000))
                if 'public_date' in self.arr_detail:
                    item['public_date'] = public_date
                if 'tag' in self.arr_detail:
                    item['tag'] = ''
                yield item

                arr_image = div_body.xpath('//img/@src').extract()
                arr_image = list(set(arr_image))
                for i in arr_image:
                    if i.find('https://i-vnexpress.vnecdn.net') + i.find('https://images.vov.vn') == 0:
                        item_image['tbl_tag'] = 'tbl_images'
                        item_image['id_picture'] = id_picture
                        item_image['image'] = i
                        yield item_image
