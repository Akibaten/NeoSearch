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

progressbar = tqdm(range(len(id_site_list) - 1))

# print(id_site_list)
site_lists = [site_list.tolist() for site_list in np.array_split(id_site_list,4)]
# print(site_lists[0])

print([len(list) for list in site_lists])

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

    def __init__(self, site_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls = [url for url in site_list]

    def start_requests(self):
        # for url in self.urls:
        yield scrapy.Request(url="https://ransei.neocities.org", callback=self.scrape_site, cb_kwargs={'site_id': 1, 'new_site': True})
    
    def scrape_site(self, response, site_id, new_site):
        if new_site:
            progressbar.update(1)
            progressbar.refresh()

        # Get all href attributes
        all_hrefs = response.css('a::attr(href)').getall()
        
        # Filter for relative URLs (don't start with http:// or https://)
        relative_urls = [response.urljoin(href) for href in all_hrefs 
                        if href and href.endswith(('.html'))
                                and not href.startswith(('http://', 'https://'))]
        word_set = set(html.fromstring(cleaner.clean_html
                            (response.text)).text_content().translate(punctuation_remover).split())
        
        #this checks if the word is in the database already
        # if not its put in with a new id
        # if it is than that id is given to the 
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
        for relative_url in relative_urls:
            yield scrapy.Request(url=relative_url, callback=self.scrape_site, cb_kwargs={'site_id': site_id, 'new_site': False})

crawler = CrawlerProcess(settings={
    'LOG_LEVEL':  'ERROR',
    
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
