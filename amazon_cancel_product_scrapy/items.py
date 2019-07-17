# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst

from .utils import RE_REVIEW_DETAILS_STAR, RE_REVIEW_DETAILS_ASIN


class AmazonCancelProductScrapyItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def get_review_details_star(value):
    star = re.search(RE_REVIEW_DETAILS_STAR, value, re.M)
    return star.group() if star else ''


def get_review_details_asin(value):
    asin = re.search(RE_REVIEW_DETAILS_ASIN, value, re.M)
    return asin.group(1) if asin else ''


class AmazonCancelProductScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    asin = scrapy.Field(
        input_processor=MapCompose(get_review_details_asin)
    )
    star = scrapy.Field()
    # star = scrapy.Field(
    #     input_processor=MapCompose(get_review_details_star)
    # )
    all_review_num = scrapy.Field(
        input_processor=MapCompose(lambda x: int(x.replace(',', '')) if x else 0)
    )
    is_image = scrapy.Field()
    # input_processor=MapCompose(lambda x: '有' if x else '没有')
    product_url = scrapy.Field()
    review_url = scrapy.Field()
    user_url = scrapy.Field()
