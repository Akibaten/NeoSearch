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
breakpoint()
site_lists = []
for site_list in np.array_split(id_site_list, 4):
    chunk = [tuple(site) for site in site_list.tolist()]
    site_lists.append(chunk)



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

    def __init__(self, site_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for url in site_list:
            pages_to_visit.append(url)

    def start_requests(self):
        yield scrapy.Request(url=self.pages_to_visit[0][1], callback=self.scrape_site, cb_kwargs={'site_id': self.pages_to_visit[0][0]})
    
    def scrape_site(self, response, site_id):
        print(self.pages_to_visit)
        print("\n\n")
        print(self.pages_visited)
        print("\n\n")
        self.pages_visited.append((site_id,response.url))

        self.pages_to_visit.popleft()
        
        #handles 404 logic
        #basically just does the callback earlierso using self.parse() doesn't throw an error
        if response.status == 404:
            yield scrapy.Request(url=self.pages_to_visit[0][1], callback=self.scrape_site, cb_kwargs={'site_id': self.pages_to_visit[0][0]})
        
        progressbar.update(1)
        progressbar.refresh()
        self.parse(response, site_id)
        print(f"intersection: {set(self.pages_to_visit).intersection(set(self.pages_visited))}")
        yield scrapy.Request(url=self.pages_to_visit[0][1], callback=self.scrape_site, cb_kwargs={'site_id': self.pages_to_visit[0][0]})

    def parse(self, response,site_id):
        
        # Get all href attributes
        all_hrefs = response.css('a::attr(href)').getall()
        # Filter for relative URLs (don't start with http:// or https://)
        for href in all_hrefs:
            if not href.startswith(('http://', 'https://','#')):
                if "." not in href or ".html" in href:
                    relative_url = response.urljoin(href)
                    if (relative_url.startswith(('http://','https://'))
                        and (site_id, relative_url) not in self.pages_to_visit
                        and (site_id, relative_url) not in self.pages_visited):
                        #appends sanitized relative url to the deque of pages to be visited
                        self.pages_to_visit.append((site_id, relative_url))   
                        
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

crawler = CrawlerProcess(settings={
    'LOG_LEVEL':  'CRITICAL',
    
    'CONCURRENT_REQUESTS': 16,

    # stop trying hanging sites forever
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 1,
    'AUTOTHROTTLE_MAX_DELAY': 10,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    'DOWNLOAD_TIMEOUT': 2,
    'RETRY_TIMES': 2
})



crawler.crawl(KeywordSpider,site_list=site_lists[0])
# crawler.crawl(KeywordSpider,site_list=site_lists[1])
# crawler.crawl(KeywordSpider,site_list=site_lists[2])
# crawler.crawl(KeywordSpider,site_list=site_lists[3])

crawler.start()

word_id_db.commit()
site_words_db.commit()

stats_db.close()
word_id_db.close()
site_words_db.close()
