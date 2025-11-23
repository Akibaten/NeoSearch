import sqlite3
import sys, getopt
from time import sleep
import os

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

site_words_db = sqlite3.connect("../data/site_words.db")
site_words_db_cursor = id_db.cursor()

neorank_db = sqlite3.connect("../data/neorank.db")
neorank_db_cursor = neorank_db.cursor()

#strictly for passing keyword argument from command line
keywords = sys.argv[1]

def search(word):

    #python REALLY dislikes me trying to grab id data and sanitize
    # a single list comprehension so it is broken up :P
    id_with_keyword = list(dict.fromkeys(id_db_cursor.execute("""
                        SELECT word,id FROM keyword_list
                        WHERE word = ?
                    """, (word,)).fetchall()))
    id_with_keyword = [tuple[1] for tuple in id_with_keyword]

    return id_with_keyword        

def rank(id_list):
    
    neorank_list = list(neorank_db_cursor.execute("""
                                    SELECT * FROM neorank                              
                                    ORDER BY rank DESC"""))

    sorted_ids = [rank[0] for rank in neorank_list
                                 if rank[0] in id_intersection]

    #i'm leaving the whole thing just to show it does actually work
    # i don't really need to generate a tuple with the rank is its already sorted
    # also list comprehension YESYESYESYSYESYESYES
    rank_tuples = [neorank_db_cursor.execute("""
                                    SELECT id, rank FROM neorank
                                    WHERE id=?
                                 """,(id,)).fetchall()[0] for id in sorted_ids]
    return rank_tuples
    
id_with_any_keyword = [search(keyword) for keyword in keywords.split()]

# woah intersection is so cool
# this sets an array that has all the ids present in every keyword set
id_intersection = list(set(id_with_any_keyword[0]).intersection(*id_with_any_keyword[1:]))

sorted_pages = [stats_db_cursor.execute("""
                        SELECT id, site_url FROM website
                        WHERE id = ?
                        """,(rank_tuple[0],)).fetchall()[0] for rank_tuple in rank(id_intersection)]

for page_tuple in sorted_pages:
    print(page_tuple[1])
    sleep(0.1)
