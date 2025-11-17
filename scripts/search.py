import sqlite3
import sys, getopt
from time import sleep
import os

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

id_db = sqlite3.connect("../data/keyword_id.db")
id_db_cursor = id_db.cursor()

neorank_db = sqlite3.connect("../data/neorank.db")
neorank_db_cursor = neorank_db.cursor()

#strictly for passing keyword argument from command line
keyword = sys.argv[1]

def search(word):

    #python REALLY dislikes me trying to grab id data and sanitize
    # a single list comprehension so it is broken up :P
    id_with_keyword = list(dict.fromkeys(id_db_cursor.execute("""
                        SELECT word,id FROM keyword_list
                        WHERE word = ?
                    """, (word,)).fetchall()))
    id_with_keyword = [tuple[1] for tuple in id_with_keyword]
            
    neorank_list = list(neorank_db_cursor.execute("""
                                SELECT * FROM neorank                              
                                ORDER BY rank DESC"""))
   
    sorted_ids = [rank[0] for rank in neorank_list if rank[0] in id_with_keyword]                            
    
    pages_with_keyword = [list(stats_db_cursor.execute("""
                                SELECT id, site_url FROM website
                                WHERE id = ?
                                                    """,(id,)))
                                for id in sorted_ids]

    unsorted_pages = [list(stats_db_cursor.execute("""
                        SELECT id, site_url FROM website
                        WHERE id = ?
                                            """,(id,)))
                        for id in id_with_keyword]

    # print(pages_with_keyword)                        
    # print(id_with_keyword)
    # print(sorted_ids)
    print("all sites:")
    sleep(1)
    for site in stats_db_cursor.execute("SELECT * FROM website"):
        print(site[1])
        sleep(.005)
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
    print("\n\n")

    print("pre sort sites:")
    sleep(1)
    for page in unsorted_pages:
        print(page[0][1])
        sleep(.1)
    print("\n\n")
    print("search results:")
    sleep(1)
    for page in pages_with_keyword:
        print(page[0][1])
        sleep(.1)
search(word=keyword)
