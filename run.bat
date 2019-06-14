@echo off & setlocal enabledelayedexpansion
cd /d %~dp0
cd amazon_cancel_product_scrapy
pipenv run python run.py
pause