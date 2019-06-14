# amazon_cancel_product_scrapy

最近接到一个奇怪的需求, 说是需要评论还在, 但是amazon 产品页面是 404 的 数据, 然后我开启了现在的爬虫之旅

设计流程是这样:

1. 通过 amazon 搜索输入框 搜索产品 爬取 相关关键词 数据
2. 根据 amazon 产品asin 获取对应 asin的评论数据 
3. 根据 评论数据 获取 amazon个人主页数据
4. 根据 个人主页查找 评论还在 产品页面404 的 数据

## 使用方法

1. 本项目采用 pipenv 作为 python 虚拟环境和依赖管理工具

2. 项目采用 阿布云 做代理 请在 middlewares.py 文件实现下

3. 执行以下命令运行本项目

```
pipenv install
```

运行 run.bat 文件

## 运行截图

![amazon_cancel_product_scrapy](https://github.com/LingHanChuJian/amazon_cancel_product_scrapy/blob/master/img/cancel.png)