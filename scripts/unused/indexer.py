import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3

stats_db = sqlite3.connect("site_stats.db")
stats_db_cursor = stats_db.cursor()

index = []

document_id_counter = 1;

def index_site(init_url,max_depth=15):

    global document_id_counter
    
    site_html = requests.get(init_url).text
    site_parser = BeautifulSoup(site_html, 'html.parser')

    index.append([init_url,document_id_counter])

    document_id_counter += 1

    
    
    for link in site_parser.find_all(href=True):
        if "https://" not in link['href'] and ".html" in link['href'] and document_id_counter < max_depth:
            if link['href'][0] == "/" :
                
                index_site(f"{init_url}{link['href']}")
            elif link['href'][0] != "/":
                print(link['href'])
                index_site(f"{init_url}/{link['href']}") 
    index.sort()

#don't use a trailing forward slash lol. breaks everything and causes loops
index_site("https://doqmeat.com")
for e in index:
    print(e)
