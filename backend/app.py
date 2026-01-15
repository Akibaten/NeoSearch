from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request
from flask_cors import CORS
from markupsafe import escape
import sqlite3
import sys, getopt
from time import sleep,time
import os
from itertools import chain
import string
import structlog
from pathlib import Path

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://searchneocities.neocities.org"
])

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/search")

def search():

    #timer for measuring how long a query takes
    query_timer_start = time()

    # opens logs for queries made for analytics reasons. This is anonymous completely of course
    structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=Path("data/query.log").with_suffix(".log").open("a")

    ),)

    query_logger = structlog.get_logger()

    #NOTE all paths with data/ are pathing to the render persistent disk mounted in the same directory as app.py
    # this means that local files and the server files have the same path
   
    stats_db = sqlite3.connect("data/site_stats.db")
    stats_db_cursor = stats_db.cursor()

    site_words_db = sqlite3.connect("data/site_words.db")
    site_words_db_cursor = site_words_db.cursor()

    word_id_db = sqlite3.connect("data/word_id.db")
    word_id_db_cursor = word_id_db.cursor()

    neorank_db = sqlite3.connect("data/neorank.db")
    neorank_db_cursor = neorank_db.cursor()

    #gets keywords for query
    query = request.args.get("q","")

    # write query to log
    query_logger.info("search", query=f"{query}")

    #deletes duplicate keywords
    keywords = set(query.lower().translate(str.maketrans('','', string.punctuation)).split())

    #converts keywords to their ids
    keywords_as_ids = [word_id_db_cursor.execute("""
                        SELECT id FROM word_id_list WHERE word=?""",(word,)).fetchone() for word in keywords]

    # may have no results so this try checks that
    keywords_as_ids = tuple([id[0] for id in keywords_as_ids])

    placeholders = ",".join("?" * len(keywords_as_ids))

    sql_query = f"""SELECT site_id
                FROM site_words_tfidf
                WHERE word_id IN ({placeholders})
                GROUP BY site_id
                HAVING COUNT(DISTINCT word_id) = {len(keywords_as_ids)}"""
                
    site_ids = [int(site_id[0]) for site_id in site_words_db_cursor.execute(sql_query, keywords_as_ids).fetchall()]

    #beginning of rank function
    
    #creates a queries with a ton of ? = to the number of elements in id_list
    placeholders = ",".join("?" * len(site_ids))


    neorank_db_cursor.execute("ATTACH DATABASE 'data/site_stats.db' AS site_stats")
    neorank_db_cursor.execute("ATTACH DATABASE 'data/site_words.db' AS site_words")
    
    #big big sql for me at least it was a little hard
    # attaches, left joins id and url to new cte selected with parameters, sorts by rank 
    sql_query = f"""WITH id_rank_cte AS(
                SELECT id, rank FROM neorank
                WHERE id IN ({placeholders}))
                SELECT id_rank_cte.id, id_rank_cte.rank, site_stats.website.id, site_stats.website.site_url, site_stats.website.profile_url,site_stats.website.site_title
                FROM id_rank_cte
                JOIN site_stats.website ON id_rank_cte.id = site_stats.website.id
                """
   
    breakpoint()
    ids_with_ranks = neorank_db_cursor.execute(sql_query, tuple(site_ids)).fetchall()
    
    tfidf_rank_ids = []
    
    #creates a ton of ? = to the number of keywords
    placeholders = ",".join("?" * len(keywords_as_ids))
    
    #query for  finding tf-idf values
    sql_query = f"SELECT tfidf FROM site_words_tfidf WHERE site_id =? AND word_id IN ({placeholders})"

    breakpoint()
    #find tf-idf values
    for site in ids_with_ranks:
        #this is a sum in the case of multiple keywords
        total_tfidf_value = sum(
                            [value[0] for value in site_words_db_cursor.execute(sql_query,
                            (site[0], *[keyword for keyword in keywords_as_ids])
                            ).fetchall()])
        
        #adding 1 here really smoothes it out because tfidf is a coefficient of rank in the sort
        tfidf_rank_ids.append((site[0],site[1]*(total_tfidf_value+1),site[3],site[4],site[5]))
    breakpoint()
    tfidf_rank_ids.sort(key=lambda x: x[1], reverse=True)
    breakpoint()
    query_timer_end = time()

    stats_db.close()
    site_words_db.close()
    word_id_db.close()
    neorank_db.close()

    #returns json of array with all sites in order
    return {'site_urls': [site[2] for site in tfidf_rank_ids],
            'profile_urls': [site[3] for site in tfidf_rank_ids],
            'site_title': [site[4] for site in tfidf_rank_ids],
            'query_duration': query_timer_end-query_timer_start,
            'ranks':[site[1] for site in tfidf_rank_ids]}
