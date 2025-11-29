from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request
from flask_cors import CORS
from markupsafe import escape
import sqlite3
import sys, getopt
from time import sleep
import os
from itertools import chain
import string

#strictly for passing keyword argument from command line
# makes keywords lowercase and removes punctuation
# keywords = sys.argv[1].lower().translate(str.maketrans('', '', string.punctuation)).split()

app = Flask(__name__)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/search")

def search():

    #NOTE all paths with /data/ are pathing to the render persistent disk
    # if you want to run locally just switch this from /data/ to data/ no starting slash
    
    stats_db = sqlite3.connect("/data/site_stats.db")
    stats_db_cursor = stats_db.cursor()

    site_words_db = sqlite3.connect("/data/site_words.db")
    site_words_db_cursor = site_words_db.cursor()

    word_id_db = sqlite3.connect("/data/word_id.db")
    word_id_db_cursor = word_id_db.cursor()

    neorank_db = sqlite3.connect("/data/neorank.db")
    neorank_db_cursor = neorank_db.cursor()

    #gets keywords for query
    query = request.args.get("q","")
    
    #deletes duplicate keywords
    keywords = set(query.lower().translate(str.maketrans('','', string.punctuation)).split())

    #converts keywords to their ids
    keywords_as_ids = [word_id_db_cursor.execute("""
                        SELECT id FROM word_id_list WHERE word=?""",(word,)).fetchone() for word in keywords]

    # may have no results so this try checks that
    keywords_as_ids = tuple([id[0] for id in keywords_as_ids])

    placeholders = ",".join("?" * len(keywords_as_ids))

    sql_query = f"""SELECT site_id
                FROM site_words
                WHERE word_id IN ({placeholders})
                GROUP BY site_id
                HAVING COUNT(DISTINCT word_id) = {len(keywords_as_ids)}"""
                
    site_ids = [int(site_id[0]) for site_id in site_words_db_cursor.execute(sql_query, keywords_as_ids).fetchall()]

    #beginning of rank function
    site_neorank_list = []

    #creates a queries with a ton of ? = to the number of elements in id_list
    placeholders = ",".join("?" * len(site_ids))


    neorank_db_cursor.execute("ATTACH DATABASE '/data/site_stats.db' AS site_stats")

    
    
    #big big sql for me at least it was a little hard
    # attaches, left joins id and url to new cte selected with parameters, sorts by rank 
    sql_query = f"""WITH id_rank_cte AS(
                SELECT id, rank FROM neorank
                WHERE id IN ({placeholders}))
                SELECT id_rank_cte.id, id_rank_cte.rank, site_stats.website.id, site_stats.website.site_url
                FROM id_rank_cte
                LEFT JOIN site_stats.website ON id_rank_cte.id = site_stats.website.id
                ORDER BY id_rank_cte.rank DESC"""
                
    ids_ranked = neorank_db_cursor.execute(sql_query, tuple(site_ids)).fetchall()
    #returns json of array with all sites in order
    return {'results': [site[3] for site in ids_ranked]}

    stats_db.close()
    site_words_db.close()
    word_id_db.close()
    neorank_db.close()
