import sqlite3
import math
from collections import Counter
from tqdm import tqdm

site_words_db = sqlite3.connect("../data/site_words.db")
site_words_db_cursor = site_words_db.cursor()
site_words_db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS site_words_tfidf(
    site_id,
    word_id,
    tfidf,
    unique(site_id,word_id)
    )
""")

word_id_db = sqlite3.connect("../data/word_id.db")
word_id_db_cursor = word_id_db.cursor()

all_words = [word_id[0] for word_id in word_id_db_cursor.execute("SELECT id FROM word_id_list").fetchall()]

#not all sites will be able to be indexed so total_sites is likely different than the total sites in just the site_stats.db
total_sites = site_words_db_cursor.execute("""
    SELECT COUNT(DISTINCT site_id) FROM site_words
""").fetchone()[0]

progressbar = tqdm(total=len(all_words))

document_frequency_data = site_words_db_cursor.execute("""
    SELECT word_id, COUNT(DISTINCT site_id) as doc_count
    FROM site_words
    GROUP BY word_id
""").fetchall()

idf_values = []

for word in document_frequency_data:
    if math.log((total_sites/(word[1])+1)) == 0:
        print("here")
        breakpoint()
    idf_values.append((math.log((total_sites)/(word[1])+1), word[0]))

idf_values = dict([(value[1],value[0]) for value in idf_values])
tfidf_values = []

sites = site_words_db_cursor.execute("""
        WITH total_words AS (
            SELECT site_id, COUNT(*) as total
            FROM site_words
            GROUP BY site_id 
        )
        SELECT 
            sw.site_id, 
            sw.word_id, 
            COUNT(*) as word_count,
            tw.total as total_words
        FROM site_words sw
        JOIN total_words tw ON sw.site_id = tw.site_id
        GROUP BY sw.site_id, sw.word_id""").fetchall()

for site in sites:
    tfidf_values.append((site[0],site[1],((site[2]/site[3])/idf_values[site[1]])))
    progressbar.n += 1
    if progressbar.n % 10 == 0:
        progressbar.refresh()
   
site_words_db_cursor.executemany("""
    INSERT INTO site_words_tfidf(site_id,word_id,tfidf)
    VALUES (?,?,?)
""",tfidf_values)

print("\n\n\nfinished calculating tf-idf")

site_words_db.commit()
site_words_db.close()
word_id_db.close()


