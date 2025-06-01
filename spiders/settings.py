# spiders/settings.py
BOT_NAME = 'flight_scraper'
SPIDER_MODULES = ['spiders.flight_spider']
NEWSPIDER_MODULE = 'spiders.flight_spider'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2

# Use SelectorEventLoop for Windows compatibility
REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"