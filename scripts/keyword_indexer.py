import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import re
import sqlite3
import string
from tqdm import tqdm
indexedwords = []
#not indexed words currently not implemented
no_index_words = [
    "the","of","and","a","to","in","is","you","that","it","he","was","for",
    "on","are","as","with","his","they","I","at","be","this","have","from",
    "or","one","had","by","word","but","not","what","all","were","we","when",
    "your","can","said","there","use","an","each","which","she","do","how",
    "their","if","will","up","other","about","out","many","then","them",
    "these","so","some","her","would","make","like","him","into","time","has",
    "look","two","more","write","go","see","number","no","way","could","people",
    "my","than","first","water","been","call","who","oil","its","now","find","long",
    "down","day","did","get","come","made","may","part"
]
stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()
id_db = sqlite3.connect("../data/keyword_id.db")
id_db_cursor = id_db.cursor()
id_db_cursor.execute(
    """CREATE TABLE IF NOT EXISTS keyword_list(
            word,
             id,
             unique(word,id))
             """)
id_site_list = stats_db_cursor.execute("""SELECT id, site_url FROM website""").fetchall()
def add_keyword(url, document_id):
    site_html = requests.get(url).content.decode("utf-8")
    site_parser = BeautifulSoup(site_html, 'html.parser')
    words = site_parser.text.translate(str.maketrans('', '', string.punctuation)).lower().split()
    # print(words)
    for word in words:
        print(f"{word} : {document_id}")
        id_db_cursor.execute(
            """INSERT OR IGNORE INTO keyword_list(word,id) VALUES
                    (?, ?)""", (word,document_id)
        )
#progress bar for my sanity lol
for site in tqdm(id_site_list):
    try:
        add_keyword(url=site[1], document_id=site[0])
        id_db.commit()
    except Exception as e:
        continue

id_db_cursor.execute("VACUUM")
