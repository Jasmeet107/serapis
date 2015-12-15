from pymongo import MongoClient
from bson.objectid import ObjectId
from termcolor import colored
import random, csv
import numpy as np

# db
client = MongoClient()
db = client.confessions

with open("time.csv", "wb") as resultsfile:
    writer = csv.DictWriter(resultsfile, fieldnames=['date', 'school', 'sentiment'])
    writer.writeheader()
    for result in db.results.find():
        parse = db.parses.find_one({ "_id": ObjectId(result["confession_id"]) })
        confession = db.confessions.find_one({ "id": parse["confession_id"] })
        writer.writerow({
            "date": confession["created_time"],
            "school": confession["school"],
            "sentiment": result["sentiment"]
        })
