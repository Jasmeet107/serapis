import facebook
import requests, requests_cache
import time, random
import config

from pymongo import MongoClient

# db
client = MongoClient()
db = client.confessions
db.confessions.drop()

# cache
requests_cache.install_cache('confessions_cache')

# authenticate with FB
access_token = facebook.get_app_access_token(config.app_id, config.app_secret)
graph = facebook.GraphAPI(access_token=access_token)

# for each confession page
for school in config.pages.keys():
    print "Getting confessions from %s" % school

    # initial confessions
    posts = graph.get_connections(id=config.pages[school], connection_name="feed")

    # paginate
    confessions = []
    while True:
        try:
            confessions.extend(posts['data'])
            # save to mongo
            for confession in posts['data']:
                confession['school'] = school
                db.confessions.insert_one(confession)

            # get next page
            posts = requests.get(posts['paging']['next']).json()
            print "%s Total: %d" % (school, len(confessions))

            # random delay to (suuuuper naively but good enough for what we need)
            # appear less roboty
            time.sleep(0.001 * random.uniform(25, 125))
        except KeyError:
            # no more pages
            break
