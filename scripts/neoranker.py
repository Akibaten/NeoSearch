import sqlite3

# neorank_list = []

# total_views = 0;

# total_followers = 0;

stats_db = sqlite3.connect("../data/site_stats.db")
stats_db_cursor = stats_db.cursor()

neorank_db = sqlite3.connect("../data/neorank.db")
neorank_db_cursor = neorank_db.cursor()

neorank_db_cursor.execute("CREATE TABLE IF NOT EXISTS neorank(id,rank)")

#finds sum of all views
total_views = stats_db_cursor.execute("""
        SELECT SUM(views) FROM website
                        """).fetchall()[0][0]

#finds sum of all follows
total_followers = stats_db_cursor.execute("""
        SELECT SUM(followers) FROM website
                                          """).fetchall()[0][0]

print(f"{total_views} {total_followers}")

def calc_neorank(site):

    global total_views
    global total_followers
    
    site_views = site[3] / total_views

    print(site_views)
    site_followers = site[4] / total_followers
    views_modifier = 1
    followers_modifier = 1

    return views_modifier  * site_views + followers_modifier * site_followers

for site in stats_db_cursor.execute("SELECT * FROM website"):
    neorank_db.execute("""
         INSERT INTO neorank VALUES
             (?,?)""",(site[0],calc_neorank(site)))

#create normalizer factor
normalizer = neorank_db_cursor.execute("""
        SELECT SUM(rank) FROM neorank
                        """).fetchall()[0][0]
print(f"{type(normalizer)} {normalizer}")


#normalize all neorank values to sum to 1 fastest in sql
neorank_db.execute("""
    UPDATE neorank SET rank=rank*(1/?)
                   """, (normalizer,))

#order the list descending
neorank_db_cursor.execute("""
    SELECT * FROM neorank
    ORDER BY rank DESC;
                   """)

#ADD A PRINT STATEMENT HERE TO LOOK AT THE ARRAY ITS BROKEN IDKDKDKDKDK
neorank_db.commit()
print(neorank_db_cursor.fetchall())
