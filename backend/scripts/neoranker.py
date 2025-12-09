import sqlite3
import math

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

    #I convert views and followers to int here
    site_views = int(site[4]) / total_views
    site_followers = int(site[5]) / total_followers
    time_since_update = int(site[6])
    views_modifier = 1
    followers_modifier = 1

    #time since the last update is weighted very *interestingly*
    # Ideally I want difference to be minimal up to about 3 months
    # and then after I want it to increase somewhat close to linearly and then get higher
    # i messed around and think that a sigmoid function is likely best for this
    time_since_update_modifier = y = 1 / (1 + math.e ** (time_since_update / 2592000))

    return time_since_update_modifier*(views_modifier  * site_views + followers_modifier * site_followers)

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

neorank_db.commit()
