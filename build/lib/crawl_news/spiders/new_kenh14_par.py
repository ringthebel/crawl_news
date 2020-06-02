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

class Kenh14Spider(scrapy.Spider):
    name = "news_kenh14"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(Kenh14Spider, self).__init__(*args, **kwargs)
        self.close_down = False
        print("category_link abc", category_link)
        if category_link == 'http://kenh14.vn/xa-hoi.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-142-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/star.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-1-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/cine.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-2-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/musik.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-3-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/doi-song.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-4-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/tv-show.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-152-0-1-1-0.chn'
        elif category_link == 'http://kenh14.vn/beauty-fashion.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-5-0-4-1-0.chn'
        elif category_link == 'http://kenh14.vn/the-gioi.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-149-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/sport.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-118-0-3-1-0.chn'
        elif category_link == 'http://kenh14.vn/hoc-duong.chn':
            self.category_link = 'http://kenh14.vn/timeline/laytinmoitronglist-{}-2-1-1-1-1-47-0-3-1-0.chn'
        else:
            print("no category link")
            # breakpoint()
        self.start_url = [self.category_link.format(1)]
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
        yield scrapy.Request(url=self.start_url[0], callback=self.parse)

    def parse(self, response):
        arr_links = response.xpath('//li')
        if len(arr_links) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        if len(arr_links) > 0:
            for arr in arr_links:
                title = ''
                link = arr.xpath('.//div[@class="knswli-right"]/h3/a/@href').extract_first()
                title = arr.xpath('.//div[@class="knswli-right"]/h3/a/@title').extract_first()

                if link is not None:
                    if link.find("http") < 0 and link != 'http://kenh14.vn':
                        link = 'http://kenh14.vn' + link
                        yield scrapy.Request(url=link, callback=self.get_detail_post,
                                             meta={
                                                    'post_title': title,
                                                   'post_link': link,
                                                   }
                                             )

            str_number = re.sub(r'([^0-9\s:\-\/]+?)', '', response.url)
            list_number = str_number.split('-')
            number_page = int(list_number[1]) + 1
            yield scrapy.Request(url=self.start_url[0].format(number_page), callback=self.parse,
                                 meta={
                                       'post_title': title,
                                       'post_link': link,
                                       }
                                 )
        else:
            raise scrapy.exceptions.CloseSpider('OVERTIME')

    def get_detail_post(self, response):
        if self.close_down:
            raise CloseSpider('OVER NUMBER_POST')

        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
        post_title = response.meta['post_title']
        post_link = response.meta['post_link']
        tag = ''
        try:
            div_tag = response.xpath('//div[@class="klw-new-tags clearfix"]/ul[@class="knt-list"]/li')
            for _ in div_tag:
                str_tag = _.xpath('./a//text()').extract_first()
                tag += str_tag.strip() + '/'
        except:
            pass
        public_date = response.xpath('//span[@class="kbwcm-time"]//text()').extract_first()
        if public_date:
            public_date = public_date.strip()
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', public_date).strip()
            public_date = datetime.strptime(
                public_date, '%H:%M %d/%m/%Y')
            public_date = public_date.timestamp() * 1000

        content = ''
        summary = ''
        author = ''
        author = response.xpath('//span[@class="kbwcm-author"]//text()').extract_first()
        author = author.strip()
        summary = response.xpath('//h2[@class="knc-sapo"]//text()').extract_first()
        if summary is not None:
            summary = summary.strip('\r\n')
            summary = summary.strip()
            if summary[-1] != '.' and (summary[-1] not in ['!', ':', ';', '?']):
                content = summary + '. '
            else:
                content = summary + ' '
        else:
            content = ''
        div_body = response.xpath('//div[@class="knc-content"]')

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

        item = CrawlNewsItem()
        item_image = ImageItem()

        if content is not None:
            item['tbl_tag'] = 'tbl_news'
            item['id_picture'] = id_picture
            if 'source_title' in self.arr_detail:
                item['source_title'] = 'kenh14'
            if 'source_link' in self.arr_detail:
                item['source_link'] = 'http://kenh14.vn/'
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
            arr_image = div_body.xpath('//img/@src').extract()
            arr_image = list(set(arr_image))
            for i in arr_image:
                if i.find('https://kenh14cdn') == 0:
                    item_image['tbl_tag'] = 'tbl_images'
                    item_image['id_picture'] = id_picture
                    item_image['image'] = i or ''
                    yield item_image

        else:
            print(response.url)