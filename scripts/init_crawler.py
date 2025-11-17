import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import sys, getopt
from tqdm import tqdm

#list of sites to be appended to site object
site_list = []

#list of previously visited sites
sites_visited = []

crawlcounter = 0

#total number of sites to crawl
sites_to_crawl = int(sys.argv[1])

#creates tqdm progress bar
progressbar = tqdm(range(sites_to_crawl))

#opens stats database 
stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

#opens document ID database where each indexed site gets a unique number
id_db = sqlite3.connect("../data/document_id.db")
id_db_cursor = id_db.cursor()

def add_to_stats_db(id,site_url,profile_url,views,followers):

    global crawlcounter
    
    stats_db_cursor.execute(
        """CREATE TABLE IF NOT EXISTS website(id, site_url, profile_url, views, followers)""")

    stats_db_cursor.execute(
        """INSERT INTO website VALUES
                (?,?, ?, ?, ?)"""
    , (id,site_url, profile_url, views, followers))
    stats_db.commit()

def crawl(url):
   
    global crawlcounter
    global site_list
    global sites_visited
    
    #refresh for progress bar
    progressbar.update(crawlcounter)
    progressbar.refresh()

    #gets the text of the neocities profile page
    site_html = requests.get(url).text
    time.sleep(0.25)

    
    site_parser = BeautifulSoup(site_html, 'html.parser')
    
    link_list = []    
        
    for link_element in site_parser.find_all('div', class_="following-list"):
        for link in link_element.find_all('a', href=True):
            link_list.append('https://neocities.org'+ link['href'])

    stat_element_list = [stat
        for stat in  site_parser.find_all("div", class_='stat')]

    #follows scheme of actual user site url, profile url, views, followers
    stats = [f"https://{site_parser.find("p", class_="site-url").get_text()}",
            url]

    #adds followers and views stats
    for stat_element in stat_element_list:
        if "followers" in str(stat_element):
            followers = int(stat_element.find('strong').get_text().replace(',', ''))
        elif "views" in str(stat_element):
            views = int(stat_element.find('strong').get_text().replace(',', ''))

    stats.append(views)
    stats.append(followers)

    add_to_stats_db(id=crawlcounter,site_url=stats[0],profile_url=stats[1],views=stats[2],followers=stats[3])
   
    for link in link_list:
        if crawlcounter >= sites_to_crawl:
            return
        elif "/follows" not in link and link not in sites_visited:
            sites_visited.append(link)
            crawlcounter += 1
            crawl(link)
            
crawl("https://neocities.org/site/kingdomofakibaten")

stats_db_cursor.execute("SELECT * FROM website")
print(stats_db_cursor.fetchall())

