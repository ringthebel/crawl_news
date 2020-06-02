import time
import re
import uuid
from scrapy.exceptions import CloseSpider
from datetime import datetime
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem

class ZingSpider(scrapy.Spider):
    name = "news_newzing"

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None,
                 number_post=None, str_detail=None, *args, **kwargs):
        super(ZingSpider, self).__init__(*args, **kwargs)
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
        print("root", response.url)
        for i in range(51):
            next_link = response.url
            next_link = next_link.replace('.html', '')
            next_link = next_link + '/trang{}.html'.format(str(i))
            yield scrapy.Request(url=next_link, callback=self.get_links)

    def get_links(self, response):
        print(response.url)
        div_body = response.xpath('//div[@class="article-list listing-layout responsive"]/article')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        for div in div_body:
            link = div.xpath('.//a/@href').extract_first()
            title = div.xpath('.//a/text()').extract_first()
            if link.find('https://news.zing.vn') < 0:
                link = 'https://news.zing.vn' + link
                yield scrapy.Request(url=link, callback=self.get_detail_post,
                                     meta={
                                         'post_title': title,
                                         'post_link': link
                                     })

    def get_detail_post(self, response):
        if self.close_down:
            raise CloseSpider('OVER NUMBER_POST')
        post_title = response.meta['post_title']
        post_link = response.meta['post_link']

        author = response.xpath('//li[@class="the-article-author"]//a/text()').extract_first()
        public_date = response.xpath('//li[@class="the-article-publish"]/text()').extract_first()
        public_date = datetime.strptime(public_date, '%H:%M %d/%m/%Y')
        public_date = public_date.timestamp() * 1000
        arr_summary = response.xpath('//p[@class="the-article-summary"]//text()').extract()
        summary = ''
        for i in arr_summary:
            i = re.sub('\s\s+', ' ', i)
            summary += i
        summary = summary.strip()
        tag = ''
        try:
            div_tag = response.xpath('//div[@p="the-article-tags"]/span')
            for _ in div_tag:
                str_tag = _.xpath('//text()').extract_first()
                tag = str_tag.strip('') + '/'
        except:
            pass
        div_content = response.xpath('//div[@class="the-article-body"]//p')
        content = ''
        for _ in div_content:
            arr_content = _.xpath('//text()').extract()
            for i in arr_content:
                i = re.sub('\s\s+', ' ', i)
                content += i.strip()

        id_picture = str(uuid.uuid1()) + str(uuid.uuid1())
        item = CrawlNewsItem()
        item_image = ImageItem()

        item['tbl_tag'] = 'tbl_news'
        item['id_picture'] = id_picture
        if 'source_title' in self.arr_detail:
            item['source_title'] = 'zingnews'
        if 'source_link' in self.arr_detail:
            item['source_link'] = 'https://news.zing.vn/'
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

        arr_image = response.xpath('//div[@class="the-article-body"]//table[@class="picture"]//img/@src').extract()
        arr_image = list(set(arr_image))
        for i in arr_image:
            if i.find('https://znews-photo.zadn.vn') == 0:
                item_image['tbl_tag'] = 'tbl_images'
                item_image['id_picture'] = id_picture
                item_image['image'] = i
                yield item_image
