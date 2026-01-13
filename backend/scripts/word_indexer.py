from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import string
from tqdm import tqdm
import scrapy
from scrapy.crawler import CrawlerProcess
from lxml import etree, html
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS # common words to filter text output with

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

site_words_db = sqlite3.connect("../data/site_words.db")
site_words_db_cursor = site_words_db.cursor()
site_words_db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_words(
            site_id,
            word_id,
            frequency)
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

pages_visited = set()

#the maximum number of links that can be put in the queue per page visit
max_href_depth = 5

sites_visited = dict()

max_site_depth = 25

punctuation_remover = str.maketrans('', '', string.punctuation)

class KeywordSpider(scrapy.Spider):
    name = "keywordspider"

    handle_httpstatus_list = [404, 403, 500]

    global pages_visited
    global pages_to_visit

    def start_requests(self):
        page = pages_to_visit[0]
        pages_to_visit.popleft()
        pages_visited.add(page)
        yield scrapy.Request(url=page[1], callback=self.scrape_site, cb_kwargs={'site_id': page[0]})
    
    def scrape_site(self, response, site_id):
        domain = re.match(r'^https?://[^/]+', response.url).group()
        if domain not in sites_visited:
            sites_visited[domain] = 0

        #handles 404 logic
        #basically just does the callback earlierso using self.parse() doesn't throw an error
        if response.status != 200: 
            next_page = pages_to_visit[0]
            pages_to_visit.popleft()
            pages_visited.add(next_page)
            yield scrapy.Request(url=next_page[1], callback=self.scrape_site, cb_kwargs={'site_id': next_page[0]})
        
        # Get href from any tag
        all_links = response.css('[href]::attr(href)').getall()

        # Get value from option tags that might be links
        option_links = response.css('option::attr(value)').getall()

        # Combine them
        all_hrefs = all_links + option_links

        # Filter for relative URLs (don't start with http:// or https://)
        hrefs_added = 0
        for href in all_hrefs:
            if hrefs_added >= max_href_depth or sites_visited[domain] >= max_site_depth:
                break

            #basic sanitation first
            href = href.encode('ascii', 'ignore').decode('ascii')

            # Skip empty, just fragments, or single characters 
            if not href or href.startswith('#') or len(href) < 2:
                continue
            
            # Skip if it's just punctuation/special chars
            if href.strip('/"\'%') == '':
                continue

            if not href.startswith(('http://', 'https://','#')) or response.url in href:
                if "." not in href.rsplit('/',1)[-1] or ".html" in href:
                    relative_url = response.urljoin(href)
                    if (relative_url.startswith(('http://','https://'))
                        and (site_id, relative_url) not in pages_to_visit
                        and (site_id, relative_url) not in pages_visited):
                        #appends sanitized relative url to the deque of pages to be visited
                        pages_to_visit.append((site_id, relative_url))   
                        hrefs_added += 1
                        sites_visited[domain] += 1

                        #increases the size of the tqdm progress progressbar
                        progressbar.total += 1
        
        text_elements = (response.css('p::text').getall()
                        + response.css('h1::text').getall()
                        + response.css('h2::text').getall())

        word_list = []
        for element in text_elements:
            for word in element.split():
                word = word.lower().translate(str.maketrans('', '', string.punctuation))
                if word not in ENGLISH_STOP_WORDS:
                    word_list.append(word)

        #tries to insert
        word_id_db_cursor.executemany("""
            INSERT OR IGNORE INTO word_id_list(word)
            VALUES (?)
            """,[(word,) for word in set(word_list)])
            

        for word in word_list:
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
        pages_visited.add(next_page)
       
        if next_page is not None:
            yield scrapy.Request(url=next_page[1], callback=self.scrape_site, errback=self.handle_error, cb_kwargs={'site_id': next_page[0]})
       
    #handles download failures
    def handle_error(self, failure):
        self.logger.error(f'Failed: {failure.value}')
        next_page = pages_to_visit[0]
        pages_to_visit.popleft()
        pages_visited.add(next_page)
        yield scrapy.Request(url=next_page[1], callback=self.scrape_site, cb_kwargs={'site_id': next_page[0]}) 

#many crawler settings here
crawler = CrawlerProcess(settings={
    'LOG_LEVEL': 'CRITICAL',
    
    'CONCURRENT_REQUESTS': 16,
    
    'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    
    # Increased timeout to give sites more time to respond
    'DOWNLOAD_TIMEOUT': 15,
        
    # More retries for connection issues
    'RETRY_TIMES': 3,
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 104],
    
    # Add user agent to avoid blocks
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    
    # DNS caching
    'DNSCACHE_ENABLED': True,
})

crawler.crawl(KeywordSpider)
crawler.crawl(KeywordSpider)
crawler.crawl(KeywordSpider)
crawler.crawl(KeywordSpider)
crawler.crawl(KeywordSpider)
crawler.crawl(KeywordSpider)

crawler.start()

word_id_db.commit()
site_words_db.commit()

stats_db.close()
word_id_db.close()
site_words_db.close()
