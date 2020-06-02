import time
import re
import uuid
from datetime import datetime
from scrapy.exceptions import CloseSpider
import scrapy
from ..items import CrawlNewsItem
from ..items import ImageItem
from scrapy_splash import SplashRequest

class VovSprider(scrapy.Spider):
    name = "news_vov"
    star_urls = [
                  "https://vov.vn",
    ]

    script = """
                function main(splash)
                    local url = splash.args.url
                    assert(splash:go(url))
                    assert(splash:wait(0.5))
                    assert(splash:runjs("$('.next')[0].click();"))
                    return {
                        html = splash:html(),
                        url = splash:url(),
                    }
                end
                """

    def __init__(self, source_title=None, source_link=None, category_title=None, category_link=None, number_post=None, str_detail=None, *args, **kwargs):
        super(VovSprider, self).__init__(*args, **kwargs)
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
        div_body = response.xpath('//div[@class="col-main"]')
        if len(div_body) == 0:
            raise CloseSpider("CATEGORY LINK NOT FOUND")
        div_posts = div_body.xpath('.//article[@class="story"]//div[@class="story__heading"]')
        if div_posts:
            for div in div_posts:
                link = div.xpath('./a/@href').extract_first()
                title = div.xpath('./a/text()').extract_first()

                if title:
                    if link.find("http") < 0:
                        link = "https://vov.vn" + link
                        yield scrapy.Request(url=link, callback=self.get_detail_post,
                                             meta={
                                                   'post_title': title,
                                                   'post_link': link,
                                             })

        arr_next_page = response.xpath('//span[@class="ctl00_mainContent_ctl00_ContentListZone_pager"]/ul/li/a/@href').extract()
        
        yield SplashRequest(
            url=response.url,
            callback=self.parse,
            meta={
                "splash": {"endpoint": "execute", "args": {"lua_source": self.script}}
            },

        )

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

        public_date = response.xpath(
            '//div[@id="ctl00_mainContent_ctl00_pnMeta"]/time/text()').extract_first()
        tag = ''
        try:
            div_tag = response.xpath('//div[@class="box-content"]/a')
            for _ in div_tag:
                str_tag = _.xpath('//text()').extract_first()
                tag = str_tag.strip('') + '/'
        except:
            pass
        if public_date:
            public_date = public_date.strip()
            public_date = public_date.split(',')
            public_date = public_date[2].strip(' ') + '-' + public_date[1].strip(' ')
            public_date = datetime.strptime(
                public_date, '%d/%m/%Y-%H:%M')
            public_date = public_date.timestamp() * 1000
        sumary_div = response.xpath(
            '//div[@class="article__sapo"]/text()').extract()
        summary = ''
        for _ in sumary_div:
            if _.strip():
                summary = _.strip()
                summary += summary
        div_body = response.xpath('//div[@class = "cms-body"]')
        content = ''
        if div_body:
            div_content = div_body.xpath('.//p')
            print(div_content.extract())
            for _ in div_content:
                text = _.xpath('.//text()').extract()
                print(text)
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
        if content is not None and len(content) > 200:
            author = response.xpath(
                '//p[@class="article__author cms-author"]//text()').extract_first()

            item = CrawlNewsItem()
            item_image = ImageItem()
            id_picture = str(uuid.uuid1()) + str(uuid.uuid1())

            item['tbl_tag'] = 'tbl_news'
            item['id_picture'] = id_picture
            if 'source_title' in self.arr_detail:
                item['source_title'] = 'vov'
            if 'source_link' in self.arr_detail:
                item['source_link'] = 'https://vov.vn/'
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
                if i.find('https://images.vov.vn') == 0:
                    item_image['tbl_tag'] = 'tbl_images'
                    item_image['id_picture'] = id_picture
                    item_image['image'] = i
                    yield item_image
