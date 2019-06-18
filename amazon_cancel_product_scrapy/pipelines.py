# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import csv
import time
import winreg

NEED = ('asin', 'star', 'all_review_num', 'is_image', 'product_url', 'review_url', 'user_url')
NEED_DOC = ('asin', '星级', '评论总数', '评论是否包含图片', '产品链接', '评论链接', '买家链接')
FILENAME = 'Amazon_Cancel_Product_%Y_%m_%d_%H_%M.csv'


class AmazonCancelProductScrapyPipeline(object):
    def __init__(self):
        file_name = time.strftime(FILENAME, time.localtime())
        self.csv_file = open(os.path.join(self.get_desktop(), file_name), 'w', newline='')
        self.writer = csv.writer(self.csv_file)
        self.writer.writerow(NEED_DOC)

    def process_item(self, item, spider):
        row_data = []
        for param in NEED:
            row_data.append(item[param])
        self.writer.writerow(row_data)
        return item

    def close_spider(self, spider):
        self.csv_file.close()

    @staticmethod
    def get_desktop():
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
        return winreg.QueryValueEx(key, "Desktop")[0]
