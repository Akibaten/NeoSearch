from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import string
from tqdm import tqdm
import numpy as np
import scrapy
from scrapy.crawler import CrawlerProcess
from lxml import etree, html
from lxml.html.clean import Cleaner

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

site_words_db = sqlite3.connect("../data/site_words.db")
site_words_db_cursor = site_words_db.cursor()
site_words_db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_words(
            site_id,
            word_id)
                            """)

word_id_db = sqlite3.connect("../data/word_id.db")
word_id_db_cursor = word_id_db.cursor()
word_id_db_cursor.execute(
    """CREATE TABLE IF NOT EXISTS word_id_list(
            word,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique(word))
            """)

id_site_list = stats_db_cursor.execute("""SELECT id, site_url FROM website""").fetchall()

progressbar = tqdm(total = len(id_site_list) - 1)

pages_to_visit = deque([site for site in id_site_list])

pages_visited = deque()

#creates lxml cleaner for later use
cleaner = Cleaner()
cleaner.style = True
cleaner.inline_style = True
cleaner.scripts = True
cleaner.javascript = True
cleaner.removetags = True

punctuation_remover = str.maketrans('', '', string.punctuation)

class KeywordSpider(scrapy.Spider):
    name = "keywordspider"

    #logic for encountering 404s
    handle_httpstatus_list = [404]

    # def __init__(self, site_list, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    global pages_visited
    global pages_to_visit

    def start_requests(self):
        page = pages_to_visit[0]
        pages_to_visit.popleft()
        pages_visited.append(page)
        yield scrapy.Request(url=page[1], callback=self.scrape_site, cb_kwargs={'site_id': page[0]})
    
    def scrape_site(self, response, site_id):
        

        #handles 404 logic
        #basically just does the callback earlierso using self.parse() doesn't throw an error
        if response.status == 404:        
            yield scrapy.Request(url=next_page[1], callback=self.scrape_site, cb_kwargs={'site_id': next_page[0]})
        
        # Get all href attributes
        all_hrefs = response.css('a::attr(href)').getall()
        # Filter for relative URLs (don't start with http:// or https://)
        for href in all_hrefs:
            if not href.startswith(('http://', 'https://','#')):
                if "." not in href or ".html" in href:
                    relative_url = response.urljoin(href)
                    if (relative_url.startswith(('http://','https://'))
                        and (site_id, relative_url) not in pages_to_visit
                        and (site_id, relative_url) not in pages_visited):
                        #appends sanitized relative url to the deque of pages to be visited
                        pages_to_visit.append((site_id, relative_url))   
                        
                        #increases the size of the tqdm progress progressbar
                        progressbar.total += 1

        word_set = list(html.fromstring(cleaner.clean_html
                            (response.text)).text_content().translate(punctuation_remover).split())
        word_set.sort()

        for word in word_set:
            #makes each word lowercase and removes punctuation            
            word = word.lower().translate(str.maketrans('', '', string.punctuation))

            #tries to insert
            word_id_db_cursor.execute("""
                INSERT OR IGNORE INTO word_id_list(word)
                VALUES (?)
                """,(word,))

            #fetches word ID
            word_id = word_id_db_cursor.execute("""
                SELECT id FROM word_id_list
                WHERE word = ?
                                    """,(word,)).fetchone()[0]

            site_words_db_cursor.execute("""
                INSERT INTO site_words(site_id,word_id)
                VALUES (?,?)                            
                                        """,(site_id,word_id))

        word_id_db.commit()
        site_words_db.commit()
        progressbar.update(1)
        progressbar.refresh()

        if len(pages_to_visit) == 0:
            print("no more pages to visit in queue")
            return

        next_page = pages_to_visit[0]
        pages_to_visit.popleft()
        pages_visited.append(next_page)
        
        yield scrapy.Request(url=next_page[1], callback=self.scrape_site, cb_kwargs={'site_id': next_page[0]})

crawler = CrawlerProcess(settings={
    'LOG_LEVEL':  'DEBUG',
    
    'CONCURRENT_REQUESTS': 16,
    
    'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',

    # stop trying hanging sites forever
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': .25,
    'AUTOTHROTTLE_MAX_DELAY': 10,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    'DOWNLOAD_TIMEOUT': 2,
    'RETRY_TIMES': 2
})

crawler.crawl(KeywordSpider)
# crawler.crawl(KeywordSpider)
# crawler.crawl(KeywordSpider)
# crawler.crawl(KeywordSpider)

crawler.start()

word_id_db.commit()
site_words_db.commit()

stats_db.close()
word_id_db.close()
site_words_db.close()
