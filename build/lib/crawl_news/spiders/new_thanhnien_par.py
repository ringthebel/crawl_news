import time
import re
import uuid
from scrapy.exceptions import CloseSpider
from datetime import datetime
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem

class ThanhnienSpider(scrapy.Spider):
    name = "news_thanhnien"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(ThanhnienSpider, self).__init__(*args, **kwargs)
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
        yield scrapy.Request(url=self.category_link, callback=self.next_page)

    def next_page(self, response):
        number_page = re.sub("[^0-9]",'', response.url) or 1
        div_nextpage = response.xpath('//span[@id="ctl00_main_ContentList1_pager"]')
        if len(div_nextpage) > 0:
            if self.category_link[-1] != '/':
                self.category_link = self.category_link + '/'
            if number_page == 1:
                next_link = self.category_link
            next_link = self.category_link + 'trang-{}.html'.format(str(number_page))
            number_page += 1
            yield scrapy.Request(url=next_link, callback=self.get_links)
            yield scrapy.Request(url=next_link, callback=self.next_page)
        else:
            raise CloseSpider()

    def get_links(self, response):
        """
                get link posts in category
                :param response:
                :return:
                """
        category = []

        div_body = response.xpath('//div[@class="relative"]/article')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for div in div_body:
            link = div.xpath('.//a/@href').extract_first()
            title = div.xpath('.//a/text()').extract_first()
            if link:
                if link.find('https://thanhnien.vn') < 0:
                    link = 'https://thanhnien.vn' + link
                    yield scrapy.Request(url=link, callback=self.get_detail_post,
                                         meta={
                                             'post_title': title,
                                             'post_link': link
                                         })
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

        author = response.xpath('//div[@class="details__author"]//a/img/@alt').extract_first()
        public_date = response.xpath('//div[@class="details__meta"]/div[@class="meta"]/time/text()').extract_first()
        public_date = datetime.strptime(public_date, '%H:%M - %d/%m/%Y')
        public_date = public_date.timestamp() * 1000

        div_body = response.xpath('//div[@class="pswp-content"]')
        arr_summary = div_body.xpath('//div[@class="sapo"]//text()').extract()
        summary = ''
        for i in arr_summary:
            i = re.sub('\s\s+', ' ', i)
            summary += i
        summary = summary.strip()
        div_content = div_body.xpath('//div[@class="cms-body detail"]/div/div')
        content = ''
        for _ in div_content:
            arr_content = _.xpath('//text()').extract()
            for i in arr_content:
                i = re.sub('\s\s+', ' ', i)
                content += i.strip()
        
        tag = ''
        try:
            div_tag = response.xpath('//div[@class="details__tags"]/a')
            for _ in div_tag:
                str_tag = _.xpath('//text()').extract_first()
                tag = str_tag.strip('') + '/'
        except:
            pass
        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
        item = CrawlNewsItem()
        item_image = ImageItem()

        item['tbl_tag'] = 'tbl_news'
        item['id_picture'] = id_picture
        if 'source_title' in self.arr_detail:
            item['source_title'] = 'thanh nien'
        if 'source_link' in self.arr_detail:
            item['source_link'] = 'https://thanhnien.vn/'
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
            item['author'] = author or ''
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
            if i.find('https://image.thanhnien.vn') == 0:
                item_image['tbl_tag'] = 'tbl_images'
                item_image['id_picture'] = id_picture
                item_image['image'] = i
                yield item_image