from pathlib import Path

import scrapy
from scrapy.crawler import CrawlerProcess

class neocitiesSpider(scrapy.Spider):
    name = "neocitiesspider"

    async def start(self):
        urls = [
            "https://akibaten.xyz"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        print(response.css("a::attr(href)").getall())

crawler = CrawlerProcess()
crawler.crawl(neocitiesSpider)
crawler.start()
