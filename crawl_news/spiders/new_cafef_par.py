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

class FCafeSpider(scrapy.Spider):
    name = "news_cafef"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(FCafeSpider, self).__init__(*args, **kwargs)
        self.close_down = False
        if category_link == 'http://cafef.vn/thoi-su.chn':
            self.category_link = 'http://cafef.vn/timeline/112/trang-{}.chn'
        elif category_link == 'http://cafef.vn/thi-truong-chung-khoan.chn':
            self.category_link = 'http://cafef.vn/timeline/31/trang-{}.chn'
        elif category_link == 'http://cafef.vn/bat-dong-san.chn':
            self.category_link = 'http://cafef.vn/timeline/35/trang-{}.chn'
        elif category_link == 'http://cafef.vn/doanh-nghiep.chn':
            self.category_link = 'http://cafef.vn/timeline/36/trang-{}.chn'
        elif category_link == 'http://cafef.vn/tai-chinh-ngan-hang.chn':
            self.category_link = 'http://cafef.vn/timeline/34/trang-{}.chn'
        elif category_link == 'http://cafef.vn/tai-chinh-quoc-te.chn':
            self.category_link = 'http://cafef.vn/timeline/32/trang-{}.chn'
        elif category_link == 'http://cafef.vn/vi-mo-dau-tu.chn':
            self.category_link = 'http://cafef.vn/timeline/33/trang-{}.chn'
        elif category_link == 'http://cafef.vn/song.chn':
            self.category_link = 'http://cafef.vn/timeline/114/trang-{}.chn'
        elif category_link == 'http://cafef.vn/thi-truong.chn':
            self.category_link = 'http://cafef.vn/timeline/39/trang-{}.chn'
        else:
            print("no category link")
            breakpoint()
        self.start_url = [self.category_link.format(1)]
        self.source_title = source_title
        self.source_link = source_link
        self.category_title = category_title
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
                link = arr.xpath('./a/@href').extract_first()
                title = arr.xpath('./a/@title').extract_first()
                if link is not None:
                    if link.find("http") < 0 and link != 'http://cafef.vn':
                        link = 'http://cafef.vn' + link
                        yield scrapy.Request(url=link, callback=self.get_detail_post,
                                             meta={
                                                   'post_title': title,
                                                   'post_link': link,
                                                   }
                                             )

            str_number = re.sub(r'([^0-9\s:\-\/]+?)', '', response.url)
            list_number = str_number.split('-')
            number_page = int(list_number[-1]) + 1
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
            div_tag = response.xpath('//div[@class="tagdetail"]/div[@class="row2"]/a')
            for _ in div_tag:
                str_tag = _.xpath('//text()').extract_first()
                tag += str_tag.strip() + '/'
        except:
            pass
        content = ''
        div_title = response.xpath('//div[@class="sp-sticky-header clearfix collapsed"]').extract() 
        if len(div_title) > 0:
            public_date = int(round(time.time() * 1000))
            update_time = int(round(time.time() * 1000))
            author = ''
            summary = ''
        else:
            div_title = response.xpath('//div[@class="sp-sticky-header clearfix"]').extract()
            if len(div_title) > 0:
                public_date = int(round(time.time() * 1000))
                author = ''
                summary = ''
            else:
                title = response.xpath('//div[@class="left_cate totalcontentdetail"]//h1/text()').extract_first()
                title = title.strip()
                public_date = response.xpath('//div[@class="sharemxh topshare"]//span//text()').extract_first()
                if public_date:
                    public_date = public_date.strip()
                    public_date = re.sub(r'([^0-9\s:\-\/]+?)', '', public_date).strip()
                    public_date = datetime.strptime(
                        public_date, '%d-%m-%Y - %H:%M')
                    public_date = public_date.timestamp() * 1000
                    author = response.xpath('//p[@class="author"]//text()').extract_first()
        title = response.xpath('//div[@class="left_cate totalcontentdetail"]/h1//text()').extract_first()
        if title is not None:
            title = title.strip('\r\n')
            title = title.strip()
            if title[-1] not in ['.', '!', ':', ';', '?']:
                content = title + '. '
            else:
                content = title + ' '
        else:
            content = ''
        summary = response.xpath('//div[@class="w640 fr clear"]/h2//text()').extract_first()
        if summary is not None:
            summary = summary.strip('\r\n')
            summary = summary.strip()
            if summary[-1] not in ['.', '!', ':', ';', '?']:
                content = summary + '. '
            else:
                content = summary + ' '
        else:
            content = ''

        div_body = response.xpath('//div[@class="contentdetail"]')

        if div_body:
            div_content = div_body.xpath('.//p')
            for _ in div_content[:len(div_content) - 2]:
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
                item['source_title'] = 'cafef'
            if 'source_link' in self.arr_detail:
                item['source_link'] = 'http://cafef.vn/'
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
                if i.find('http://cafefcdn.com') == 0:
                    item_image['tbl_tag'] = 'tbl_images'
                    item_image['id_picture'] = id_picture
                    item_image['image'] = i or ''
                    yield item_image

        else:
            print(response.url)
