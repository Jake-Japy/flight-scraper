BOT_NAME = 'FlightStatScraper'
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2

# Retry settings to match original tenacity retry logic
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Use SelectorEventLoop for Windows compatibility
REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"