import sqlite3
import sys, getopt
from time import sleep
import os
from itertools import chain
import string

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

site_words_db = sqlite3.connect("../data/site_words.db")
site_words_db_cursor = site_words_db.cursor()

word_id_db = sqlite3.connect("../data/word_id.db")
word_id_db_cursor = word_id_db.cursor()

neorank_db = sqlite3.connect("../data/neorank.db")
neorank_db_cursor = neorank_db.cursor()

#strictly for passing keyword argument from command line
# makes keywords lowercase and removes punctuation
keywords = sys.argv[1].lower().translate(str.maketrans('', '', string.punctuation)).split()

def search(*args):
    #deletes duplicate keywords
    keywords = set(args)

    print(keywords)
    #converts keywords to their ids
    keywords_as_ids = [word_id_db_cursor.execute("""
                        SELECT id FROM word_id_list WHERE word=?""",(word,)).fetchone() for word in keywords]

    # may have no results so this try checks that
    keywords_as_ids = tuple([id[0] for id in keywords_as_ids])

    placeholders = ",".join("?" * len(keywords_as_ids))

    query = f"""SELECT site_id
                FROM site_words
                WHERE word_id IN ({placeholders})
                GROUP BY site_id
                HAVING COUNT(DISTINCT word_id) = {len(keywords_as_ids)}"""
                
    site_ids = [int(site_id[0]) for site_id in site_words_db_cursor.execute(query, keywords_as_ids).fetchall()]

    return site_ids
    
def rank(id_list):

    site_neorank_list = []

    #creates a queries with a ton of ? = to the number of elements in id_list
    placeholders = ",".join("?" * len(id_list))


    neorank_db_cursor.execute("ATTACH DATABASE '../data/site_stats.db' AS site_stats")

    
    
    #big big sql for me at least it was a little hard
    # attaches, left joins id and url to new cte selected with parameters, sorts by rank 
    query = f"""WITH id_rank_cte AS(
                SELECT id, rank FROM neorank
                WHERE id IN ({placeholders}))
                SELECT id_rank_cte.id, id_rank_cte.rank, site_stats.website.id, site_stats.website.site_url, site_stats.website.profile_url, site_title
                FROM id_rank_cte
                LEFT JOIN site_stats.website ON id_rank_cte.id = site_stats.website.id
                ORDER BY id_rank_cte.rank DESC"""
                
    ids_ranked = neorank_db_cursor.execute(query, tuple(id_list)).fetchall()

    return ids_ranked
    
#a search may have no results. In that case this breaks out of everything and says no results
try:
    site_ids = search(*keywords)
    ids_ranked = rank(site_ids)
    for site in ids_ranked[:]:
        print(f"{site[3]} {site[4]} {site[5]}")
except Exception as e:
    print(e)
    print("No results found :( maybe try a different search >w<")
