import requests
from bs4 import BeautifulSoup
from pathlib import Path
import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import sys, getopt
from tqdm import tqdm
import gc

#list of previously visited sites
sites_visited = set()

crawlcounter = 0

#first profile to crawl
init_profile = "https://neocities.org/site/lilithdev"

#total number of sites to crawl
number_of_sites_to_crawl = int(sys.argv[1])

#creates tqdm progress bar
progressbar = tqdm(range(number_of_sites_to_crawl))

#opens stats database 
stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

#creates deque queue for sites crawler needs to visit and appends first url
sites_to_visit = deque()
sites_to_visit.append(init_profile)

#set of sites visited sometimes scrapy doesn't catch it for some reason
sites_visited = set()

#opens a website crawl log file to paste the deque and site name to and clears it
# so it can be tailed while the crawler is running
crawl_log = open("../logs/crawl_log.txt", "w")

crawl_log = open("../logs/crawl_log.txt", "a")

#scrapy Spider
class NeocitiesSpider(scrapy.Spider):
       
    name = "neocitiesspider"

    handle_httpstatus_list = [404]
    
    async def start(self):

        global crawlcounter
        
        url = sites_to_visit[0]
        crawlcounter += 1
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):

        global number_of_sites_to_crawl
        global crawlcounter
        global sites_visited
        global sites_to_visit
        global crawl_log


        if response.status == 404:
            sites_visited.add(sites_to_visit[0])
            sites_to_visit.popleft()
            if sites_to_visit:
                yield scrapy.Request(url=sites_to_visit[0], callback=self.parse)
            return

        
        try:
            profile_views = int(response.css("div.stat strong::text").getall()[0].replace(',',''))
            profile_followers = int(response.css("div.stat strong::text").getall()[1].replace(',',''))
            user_site_url = response.css("p.site-url a::attr(href)").get()

            sites_visited.add(sites_to_visit[0])
            
            for link in response.css("div.following-list a::attr(href)").getall()[1:-2]:
                if (f"https://neocities.org{link}" not in sites_visited and
                    f"https://neocities.org{link}" not in sites_to_visit):
                    sites_to_visit.append(f"https://neocities.org{link}")
               # print(scrapy.Request(url=f"https://neocities.org{link}follows", callback=self.parse))
                # yield scrapy.Request(url=link, callback=self.parse)
            
            add_to_stats_db(id=crawlcounter,
                            site_url= user_site_url,
                            profile_url= sites_to_visit[0],
                            views = profile_views,
                            followers=profile_followers)
        
            if crawlcounter <= number_of_sites_to_crawl:
                crawlcounter += 1
                progressbar.update(1)
                progressbar.refresh()
                crawl_log.write(f"""{str([*sites_to_visit][0:3])}\n
                                  {sites_to_visit[0]} \n
                                  {profile_views} \n
                                  {profile_followers} \n \n
                                  {progressbar}""")
                            
                sites_to_visit.popleft()
                try:
                    yield scrapy.Request(url=sites_to_visit[0], callback=self.parse)
                except:
                    sites_visited.add(sites_to_visit[0])
                    sites_to_visit.popleft()
                    sites_to_visit.popleft()
                    yield scrapy.Request(url=sites_to_visit[1], callback=self.parse)

                    
        except Exception as e:
            sites_visited.add(sites_to_visit[0])
            sites_to_visit.popleft()
            sites_to_visit.popleft()
            yield scrapy.Request(url=sites_to_visit[1], callback=self.parse)
            
def add_to_stats_db(id,site_url,profile_url,views,followers):

    global crawlcounter
    
    stats_db_cursor.execute(
        """CREATE TABLE IF NOT EXISTS website(id, site_url, profile_url, views, followers)""")

    stats_db_cursor.execute(
        """INSERT INTO website VALUES
                (?,?, ?, ?, ?)"""
    , (id,site_url, profile_url, views, followers))
    stats_db.commit()

crawler = CrawlerProcess(settings={
    'DOWNLOAD_DELAY': 0.25,
    'LOG_LEVEL':  'DEBUG',
    
    # GRRRRR This is important
    # with multiple concurrent requests
    # sometimes in edge cases duplicates
    # will accidentally bypass the filter
    'CONCURRENT_REQUESTS': 1,

    'meta' : {'dont_redirect': True},

    'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
})

crawler.crawl(NeocitiesSpider)
crawler.start()

crawl_log.close()
stats_db.close()
progressbar.close()

gc.collect()
