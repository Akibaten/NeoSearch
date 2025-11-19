import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import sys, getopt
from tqdm import tqdm
import gc

#list of previously visited sites
sites_visited = []

crawlcounter = 0

#first profile to crawl
init_profile = "https://neocities.org/site/vanillamilkshake"

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

#opens a website crawl log file to paste the deque and site name to and clears it
# so it can be tailed while the crawler is running
crawl_log = open("../logs/crawl_log.txt", "w").close

crawl_log = open("../logs/crawl_log.txt", "a")

def add_to_stats_db(id,site_url,profile_url,views,followers):

    global crawlcounter
    
    stats_db_cursor.execute(
        """CREATE TABLE IF NOT EXISTS website(id, site_url, profile_url, views, followers)""")

    stats_db_cursor.execute(
        """INSERT INTO website VALUES
                (?,?, ?, ?, ?)"""
    , (id,site_url, profile_url, views, followers))
    stats_db.commit()

def crawler(url):

    global crawlcounter
    global sites_visited

    #gets the text of the neocities profile page
    site_html = requests.get(url).text
    time.sleep(.25)

    site_parser = BeautifulSoup(site_html, 'html.parser')
      
    link_list = []

    for link_element in site_parser.find_all('div', class_="following-list"):
        for link in link_element.find_all('a', href=True):
            try:
                if "/follows" not in link['href']:
                    link_list.append('https://neocities.org'+ link['href'])
            except Except as e:
                break
            
    #adds links found on sites to deque sites_to_visit
    for link in link_list:
        if link not in sites_visited and link not in sites_to_visit:
            sites_to_visit.append(link)

    #removes the first element of the deque (the site that is being crawled here)
    sites_to_visit.popleft()


    #NOTE Deque is implemented now. I have not tested if it works as it crawl
    # and nothing has been setup to create a looping crawl process lol
    # i've just been doing breakpoints and checking to make sure the deque is working


    stat_element_list = [stat
        for stat in  site_parser.find_all("div", class_='stat')]

    #follows scheme of actual user site url, profile url, views, followers
    stats = [f"https://{site_parser.find("p", class_="site-url").get_text()}",
            url]

    #adds followers and views stats
    for stat_element in stat_element_list:
        if "followers" in str(stat_element):
            followers = int(stat_element.find('strong').get_text().replace(',', ''))
        elif "follower" in str(stat_element):
            followers = "1"
        elif "views" in str(stat_element):
            views = int(stat_element.find('strong').get_text().replace(',', ''))

    stats.append(views)

    try:
        stats.append(followers)
    except Exception as e:
        print(followers)

    #remove site parser object
    # IF YOU DONT DO THIS IS WILL SEGFAULT a;alierwhg;laisherg;oiawheg
    # shoutout to claude for figuring this out lol
    site_parser.decompose()
    
    #adds stats to database
    add_to_stats_db(id=crawlcounter,site_url=stats[0],profile_url=stats[1],views=stats[2],followers=stats[3])

    crawlcounter += 1

    sites_visited.append(url)

#start of crawling
crawler(init_profile)

progressbar.update(1)
progressbar.refresh()

while crawlcounter < number_of_sites_to_crawl :
    #write to log
    crawl_log.write(f"{str([*sites_to_visit][0:3])} \n {sites_to_visit[0]} \n \n ")
    crawl_log.flush()
  
    #crawls
    crawler(sites_to_visit[0])
    gc.collect()

    progressbar.update(1)
    progressbar.refresh() 
 
stats_db_cursor.execute("SELECT * FROM website")

"""
all of this is also required for it to not segfault
I have no clue what is going on under the hood
probably beautifulsoup mishandling its instances
and python gets confused idk
if any gc.collect is removed the program will segfault
"""

crawl_log.close()
stats_db.close()
progressbar.close()

gc.collect()
