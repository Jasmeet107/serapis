from pymongo import MongoClient
from bson.objectid import ObjectId
from termcolor import colored
import random, csv
import numpy as np

# db
client = MongoClient()
db = client.confessions

# iterate over confessions and aggregate by category
categories = {}

for result in db.results.find():
    confession = db.parses.find_one({ "_id": ObjectId(result["confession_id"]) })
    for category, (sentiment, variance, probability) in result["categories"].items():
        if category not in categories: categories[category] = []
        categories[category].append((sentiment, variance))

with open("categories.csv", "wb") as resultsfile:
    field_names = ['category', 'sentiment', 'variance', 'total']
    writer = csv.DictWriter(resultsfile, fieldnames=field_names)
    writer.writeheader()

    # save results to CSV
    for category, data in categories.items():
        sentiments = [s for (s, v) in data]
        variances = [v for (s, v) in data]
        # MATLAB formats underscores specially
        if category == "mental_health": category = "mental health"
        datum = {
            "category": category,
            "sentiment": np.mean(sentiments),
            "variance": np.var(sentiments),
            "total": len(sentiments)
        }
        writer.writerow(datum)
