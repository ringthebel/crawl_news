import re
import time
import uuid
from scrapy.exceptions import CloseSpider
from datetime import datetime
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem

class NhandanSpider(scrapy.Spider):
    name = "news_nhandan"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None, number_post=None,
                 str_detail=None, *args, **kwargs):
        super(NhandanSpider, self).__init__(*args, **kwargs)
        self.close_down = False
        self.source_title = source_title
        self.source_link = source_link
        self.category_title = category_title
        self.category_link = category_link
        self.str_detail = str_detail
        if str_detail != None:
            self.arr_detail = self.str_detail.split(',')

    def start_requests(self):
        if self.category_link in ['https://nhandan.com.vn/hanoi', 'https://nhandan.com.vn/tphcm']:
            yield scrapy.Request(url=self.category_link, callback=self.get_links_tp)
        yield scrapy.Request(url=self.category_link, callback=self.get_links)

    def get_links_tp(self, response):
        div_body = response.xpath('//div[@class="col-sm-8 col-xs-12"]')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for div in div_body:
            title = div.xpath('.//a/text()').extract_first()
            if title == None:
                title = ''
            link = div.xpath('.//a/@href').extract_first()
            if link[-1].find("http") < 0:
                link_ = 'https://nhandan.com.vn' + link
                yield scrapy.Request(url=link_, callback=self.get_detail_post_tp,
                                     meta={
                                           'post_title': title,
                                           'post_link': link,
                                           })
            else:
                print("Notlink", response.url)
        arr_next_page = response.xpath('//div[@class="col-lg-6 col-md-6 col-xs-12 col-sm-12"]/ul/li/a/@href').extract()
        if arr_next_page[-1] is not None:
            if arr_next_page[-1].find("http") < 0:
                next_page = 'https://nhandan.com.vn' + arr_next_page[-1]
                print("nextpage", next_page)
            else:
                next_page = arr_next_page[-1]
            yield scrapy.Request(url=next_page, callback=self.get_links_tp)

    def get_detail_post_tp(self, response):
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
        div_body = response.xpath('//div[@class="media"]//tr//text()')
        date = response.xpath('//div[@class="icon_date_top"]/div[@class="pull-left"]//text()').extract_first()
        if date:
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', date.strip())
            public_date = datetime.strptime(
                public_date, '  %d/%m/%Y %H:%M:%S')
            public_date = public_date.timestamp() * 1000
        else:
            public_date = ''
        summary = response.xpath('//div[@class="ndcontent ndb"]//text()').extract_first()
        if summary:
            div_body = response.xpath('//div[@class="ndcontent"]')
        if summary:
            content = summary
        else:
            content = ''
        if div_body:
            div_content = div_body.xpath('.//p')
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

        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())

        item = CrawlNewsItem()
        item_image = ImageItem()
        if content:
            item['tbl_tag'] = 'tbl_news'
            item['id_picture'] = id_picture
            if 'source_title' in self.arr_detail:
                item['source_title'] = 'nhan dan'
            if 'source_link' in self.arr_detail:
                item['source_link'] = 'https://nhandan.com.vn/'
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

            arr_image = div_body.xpath('//img[@class="nd_img"]/@src').extract()
            for i in arr_image:
                item_image['tbl_tag'] = 'tbl_images'
                item_image['id_picture'] = id_picture
                item_image['image'] = i
                yield item_image


    def get_links(self, response):
        category = []
        div_link = response.xpath('//div[@class="hotnew-container lop3"]/div[@class="media content-box"]')
        if len(div_link) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for div in div_link:
            link = div.xpath('./h5/a/@href').extract_first()
            title = div.xpath('./h5/a/text()').extract_first()
            if link:
                category.append((title, link))
        for _ in category:
            if _[1].find("http") < 0:
                url = 'https://nhandan.com.vn' + _[1]
            yield scrapy.Request(url=url, callback=self.get_detail_post,
                                 meta={
                                     'post_title': _[0],
                                     'post_link': _[1],
                                     })
        arr_next_page = response.xpath(
            '//div[@class="media-body"]/ul[@class="pagination"]/li/a/@href').extract()
        if arr_next_page[-1] is not None:
            if arr_next_page[-1].find("http") < 0:
                next_page = 'https://nhandan.com.vn' + arr_next_page[-1]
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

        content = ''
        summary = ''
        post_title = response.meta['post_title']
        post_link = response.meta['post_link']
        div_content = response.xpath('.//div[@class="item-container"]')
        tag = ''
        date = div_content.xpath(
            '//h5[@class="date-created"]/text()').extract_first()

        if date:
            public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', date.strip())
            public_date = datetime.strptime(
                public_date, '  %d/%m/%Y %H:%M:%S')
            public_date = public_date.timestamp() * 1000
        else:
            public_date = ''
        summary = div_content.xpath('//div[@class="sapo"]/p/text()').extract_first()
        if summary:
            content = summary
        else:
            content = ''
        div_body = div_content.xpath('//div[@class="item-content"]')
        if div_body:
            div_content = div_body.xpath('.//p')
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
        author = div_content.xpath('./p[@class="text-right author"]/text()').extract_first()

        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())

        item = CrawlNewsItem()
        item_image = ImageItem()

        item['tbl_tag'] = 'tbl_news'
        item['id_picture'] = id_picture
        if 'source_title' in self.arr_detail:
            item['source_title'] = 'nhan dan'
        if 'source_link' in self.arr_detail:
            item['source_link'] = 'https://nhandan.com.vn/'
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

        arr_image = div_body.xpath('//img[@class="mr-3 img-responsive"]/@src').extract()
        arr_image = list(set(arr_image))
        for i in arr_image:
            if i.find('cdn/vn/media') == 0:
                item_image['tbl_tag'] = 'tbl_images'
                item_image['id_picture'] = id_picture
                item_image['image'] = i
                yield item_image
