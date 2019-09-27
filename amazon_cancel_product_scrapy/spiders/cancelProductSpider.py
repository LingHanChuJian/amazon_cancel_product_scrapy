import re
import json
import scrapy
from scrapy.http import Request, FormRequest
from amazon_cancel_product_scrapy.items import AmazonCancelProductScrapyItemLoader, AmazonCancelProductScrapyItem
from urllib.parse import quote

from ..utils import *
from ..log import log


class CancelProductSpider(scrapy.Spider):
    name = 'amazon_cancel_product_scrapy'

    def start_requests(self):
        log('amazon国家简码示意: \n%s'
              % '\n'.join(['%s--%s' % (item, AMAZON_DOMAIN[item]['msg']) for item in list(AMAZON_DOMAIN.keys())]))
        country = input('请输入国家简码(大小写都可以, 默认 US): ')
        if not country:
            country = 'US'
        country = country.upper().strip()
        while True:
            keyword = input('请输入amazon搜索关键字: ')
            if keyword:
                break
            else:
                log('请输入关键词 !!!')
        cur_country_data = AMAZON_DOMAIN[country]
        log('amazon搜索条件(输入数字): \n%s'
              % '\n'.join(['%s--%s' % (index, item)
                           for index, item in enumerate(cur_country_data['aliasText'])]))
        alias = input('请输入搜索条件(默认 0): ')
        if not alias:
            alias = 0
        max_page = input('请输入搜索页数(默认所有): ')
        url = amazon_url_api['search'].format(domain=cur_country_data['domain'],
                                              alias=cur_country_data['alias'][int(alias)], keyword=keyword)
        yield Request(url=cur_country_data['domain'],
                      meta={'country': country, 'max_page': max_page,
                            'url': quote(url, ':?=/&'), 'cookiejar': COOKIE_NUM},
                      headers=START_REQUESTS_HEADERS, callback=self.address_requests)

    def address_requests(self, response):
        cur_data = response.meta
        if self.is_robot(response):
            log('机器人验证')
            return None
        zip_code = AMAZON_DOMAIN[cur_data['country']]['zipCode']
        form_data = {
            'locationType': 'LOCATION_INPUT',
            'zipCode': zip_code,
            'storeContext': 'generic',
            'deviceType': 'web',
            'pageType': 'Gateway',
            'actionSource': 'glow'
        }
        if cur_data['country'] == 'AE':
            del form_data['zipCode']
            form_data['locationType'] = 'CITY'
            form_data['city'] = zip_code
            form_data['cityName'] = zip_code
        yield FormRequest(url=amazon_url_api['address'].format(domain=AMAZON_DOMAIN[cur_data['country']]['domain']),
                          headers=ADDRESS_REQUESTS_HEADERS, formdata=form_data,
                          meta=cur_data, callback=self.search_requests)

    def search_requests(self, response):
        cur_data = response.meta
        if self.is_json(response.text):
            address = json.loads(response.text)
            is_country = cur_data['country'] == 'AU'
            is_address = 'address' in address and 'zipCode' in address['address']
            if is_country or is_address:
                log('国家为AU, 需要登陆才能更换地址') if is_country else log('更换对应国家地址')
                yield Request(url=cur_data['url'], headers=SEARCH_REQUESTS_HEADERS,
                              meta=cur_data, callback=self.review_requests)
            else:
                log('更换地址失败')
        else:
            log('返回数据不是 json')

    def review_requests(self, response):
        cur_data = response.meta
        if self.is_robot(response):
            log('机器人验证')
            return None
        for i, item in enumerate(response.xpath('//div[@data-asin]/@data-asin')):
            cur_data['cookiejar'] = COOKIE_NUM + 1 + i
            yield Request(url=amazon_url_api['review']
                          .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'], asin=item.extract()),
                          headers=REVIEW_REQUESTS_HEADERS, meta=cur_data, callback=self.user_requests)
        search_next_api = self.get_next_page(response)
        cur_page = self.get_cur_search_page(response)
        max_page = cur_data['max_page']
        if not search_next_api:
            log('搜索页面, 已经达到最大翻页数, 没有下一页了')
            return None
        if not max_page:
            log('搜索页面, 准备爬取第{page}页搜索数据'.format(page=int(cur_page) + 1))
            yield Request(url='{domain}{search_next_api}'
                          .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'], search_next_api=search_next_api),
                          headers=REVIEW_REQUESTS_HEADERS,meta=cur_data, callback=self.review_requests)
        else:
            if int(cur_page) <= int(max_page):
                log('搜索页面 , 准备爬取第{page}页搜索数据'.format(page=int(cur_page) + 1))
                yield Request(url='{domain}{search_next_api}'
                              .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'],
                                      search_next_api=search_next_api), headers=REVIEW_REQUESTS_HEADERS,
                              meta=cur_data, callback=self.review_requests)
            else:
                log('搜索页面 ,已到达设置的指定页数, 不会进行继续爬取了')

    def user_requests(self, response):
        cur_data = response.meta
        if self.is_robot(response):
            log('机器人验证')
            return None
        review_data = response.xpath('//div[@data-hook="review"]')
        for review in review_data:
            review_buyer = review.xpath('div/div/div[@data-hook="genome-widget"]/a/@href')
            yield Request(url='{domain}{review_buyer}'
                          .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'],
                                  review_buyer=review_buyer.extract_first('')),
                          headers=USER_REQUESTS_HEADERS, meta=cur_data, callback=self.user_review_requests)
        review_next_api = self.get_next_page(response)
        review_cur_page = self.get_cur_review_page(response)
        if not review_next_api:
            log('产品评论页面, 已经达到最大翻页数, 没有下一页了')
            return None
        log('产品评论页面, 准备爬取第{page}页评论数据'.format(page=review_cur_page + 1))
        yield Request(url='{domain}{review_next_api}'
                      .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'], review_next_api=review_next_api),
                      headers=USER_REQUESTS_HEADERS, meta=cur_data, callback=self.user_requests)

    def user_review_requests(self, response):
        cur_data = response.meta
        if self.is_robot(response):
            log('机器人验证')
            return None
        if self.is_json(response.text):
            user_review_data = json.loads(response.text)
            if 'contributions' in user_review_data:
                for item in user_review_data['contributions']:
                    if 'product' in item and 'externalId' in item and 'link' in item['product'] \
                            and not item['product']['link']:
                        yield Request(amazon_url_api['review_details'].format(
                            domain=AMAZON_DOMAIN[cur_data['country']]['domain'], reviewId=item['externalId']),
                            headers=REVIEW_DETAILS_HEADERS, meta=cur_data)
            user_review_next_page = self.get_user_review_next_page_token(response)
            if not user_review_next_page:
                log('用户评论页面, 没有下一页了')
                return None
            log('用户评论页面, 准备获取下一页数据')
            yield Request(url=quote(amazon_url_api['user_review']
                          .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'],
                                  next_token=user_review_next_page, type=cur_data['types'],
                                  directedId=cur_data['directed_id'], token=cur_data['token']), ':?=/&'),
                          headers=USER_REVIEW_REQUESTS_HEADERS, meta=cur_data, callback=self.user_review_requests)
        else:
            token = self.get_user_review_token(response)
            types = self.get_user_review_type(response)
            directed_id = self.get_user_review_directed_id(response)
            cur_data['token'] = token
            cur_data['types'] = types
            cur_data['directed_id'] = directed_id
            yield Request(url=quote(amazon_url_api['user_review']
                          .format(domain=AMAZON_DOMAIN[cur_data['country']]['domain'],
                                  next_token='', type=types, directedId=directed_id, token=token), ':?=/&'),
                          headers=USER_REVIEW_REQUESTS_HEADERS,
                          meta=cur_data, callback=self.user_review_requests)

    def parse(self, response):
        cur_data = response.meta
        if self.is_robot(response):
            log('机器人验证')
            return None
        is_asin_404 = response.xpath('//img[@data-a-hires]/@src').extract_first('')
        if is_asin_404.find('no-img-lg') <= -1:
            log('asin 被人占用')
            return None
        amazon_item = AmazonCancelProductScrapyItemLoader(item=AmazonCancelProductScrapyItem(), response=response)
        is_image = response.xpath('//div[@class="review-image-tile-section"]').extract_first('')
        product_url = response.xpath('//a[@data-hook="product-link"]/@href').extract_first('')
        user_url = response.xpath('//a[@class="a-profile"]/@href').extract_first('')
        star = response.xpath('//i[@data-hook="average-star-rating"]//text()').extract_first('')
        star_value = re.compile(RE_REVIEW_DETAILS_STAR).findall(star)
        if cur_data['country'] == 'JP':
            star_value = star_value[-1] if len(star_value) == 2 else 0
        else:
            star_value = star_value[0]
        amazon_item.add_xpath('asin', '//a[@data-hook="product-link"]/@href')
        amazon_item.add_value('star', [star_value])
        # amazon_item.add_xpath('star', '//span[@data-hook="rating-out-of-text"]//text()')
        amazon_item.add_xpath('all_review_num', '//span[@data-hook="total-review-count"]//text()')
        amazon_item.add_value('is_image', ['有' if is_image else '没有'])
        amazon_item.add_value('product_url', ['{domain}{product_url}'.format(
            domain=AMAZON_DOMAIN[cur_data['country']]['domain'], product_url=product_url)])
        amazon_item.add_value('review_url', [response.url])
        amazon_item.add_value('user_url', ['{domain}{user_url}'.format(
            domain=AMAZON_DOMAIN[cur_data['country']]['domain'], user_url=user_url)])
        yield amazon_item.load_item()

    @staticmethod
    def is_robot(response):
        robot = response.xpath('//form[@action="/errors/validateCaptcha"]')
        return True if robot else False

    @staticmethod
    def is_json(data):
        try:
            if data and type(data) == str:
                json.loads(data)
                return True
        except Exception as e:
            print(e)
        return False

    @staticmethod
    def get_cur_search_page(response):
        cur_page = response.xpath('//li[contains(@class, "a-selected")]//text()').extract_first('')
        return int(cur_page) if cur_page else 1

    @staticmethod
    def get_cur_review_page(response):
        cur_page = re.search(RE_REVIEW_PAGE, response.url, re.M)
        return int(cur_page.group(1)) if cur_page else 1

    @staticmethod
    def get_next_page(response):
        next_page = response.xpath('//li[contains(@class, "a-last")]')
        if 'a-disabled' in next_page.xpath('@class').extract():
            return None
        return next_page.xpath('a/@href').extract_first('')

    @staticmethod
    def get_user_review_token(response):
        token = re.search(RE_USER_REVIEW_TOKEN, response.text, re.M)
        return token.group(1) if token else ''

    @staticmethod
    def get_user_review_type(response):
        types = re.search(RE_USER_REVIEW_TYPE, response.text, re.M)
        return ','.join(eval(types.group(1))) if types else ''

    @staticmethod
    def get_user_review_directed_id(response):
        directed_id = re.search(RE_USER_REVIEW_DIRECTED_ID, response.text, re.M)
        return directed_id.group(1) if directed_id else ''

    @staticmethod
    def get_user_review_next_page_token(response):
        review_data = json.loads(response.text)
        if 'nextPageToken' in review_data and review_data['nextPageToken']:
            return review_data['nextPageToken']
        return ''

