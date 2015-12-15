from pymongo import MongoClient
from bson.objectid import ObjectId
from termcolor import colored
import random, csv
import numpy as np

# db
client = MongoClient()
db = client.confessions

# iterate over confessions and aggregate by school
schools = {}
school_totals = {}

for result in db.results.find():
    categories = result["categories"]
    confession = db.parses.find_one({ "_id": ObjectId(result["confession_id"]) })
    if confession["school"] not in schools: schools[confession["school"]] = []
    schools[confession["school"]].append(categories)

    # school-level sentiment
    if confession["school"] not in school_totals: school_totals[confession["school"]] = []
    school_totals[confession["school"]].append(result["sentiment"])

# iterate through schools and average by category
with open("school.csv", "wb") as resultsfile:
    categories = ['relationships', 'sex', 'mental_health', 'social', 'sports', 'housing', 'drugs', 'academics', 'politics']
    field_names = ['school', 'sentiment', 'variance']
    for category in categories:
        field_names.append("%s_sentiment" % category)
        field_names.append("%s_variance" % category)
        field_names.append("%s_membership" % category)
    writer = csv.DictWriter(resultsfile, fieldnames=field_names)
    writer.writeheader()

    for school, results in schools.items():
        categories = {}
        for result in results:
            for category, (sentiment, variance, probability) in result.items():
                # (sentiment, variance, probability, count)
                # sum here and divide by count after
                if category not in categories: categories[category] = [[], 0]
                categories[category][0].append(sentiment)
                categories[category][1] += probability
        for category in categories.keys():
            # sentiment mean, sentiment variance, probability
            categories[category] = (np.mean(categories[category][0]), np.var(categories[category][0]), float(categories[category][1]) / len(school_totals[school]))

        # average sentiment by confession
        average_sentiment = np.mean(school_totals[school])
        average_variance = np.var(school_totals[school])

        # save results to CSV
        datum = {
            "school": school,
            "sentiment": average_sentiment,
            "variance": average_variance
        }
        for category, result in categories.items():
            datum["%s_sentiment" % category] = result[0]
            datum["%s_variance" % category] = result[1]
            datum["%s_membership" % category] = result[2]
        writer.writerow(datum)
