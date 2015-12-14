from pymongo import MongoClient
from bson.objectid import ObjectId
from termcolor import colored
import random

# db
client = MongoClient()
db = client.confessions

# iterate over confessions and aggregate by school
schools = {}
school_totals = {}

confessions = list(db.results.find())
random.shuffle(confessions)
for result in db.results.find():
    categories = result["categories"]
    confession = db.parses.find_one({ "_id": ObjectId(result["confession_id"]) })
    if confession["school"] not in schools: schools[confession["school"]] = []
    schools[confession["school"]].append(categories)

    # print colored(confession["message"], "cyan")
    # for category, probability in categories.items():
        # print "%s: %s" % (colored(category, "yellow"), colored(probability, "blue"))
    # print

    if confession["school"] not in school_totals: school_totals[confession["school"]] = [0, 0]
    school_totals[confession["school"]][0] += result["sentiment"]
    school_totals[confession["school"]][1] += 1

# iterate through schools and average by category
for school, results in schools.items():
    categories = {}
    for result in results:
        for category, (sentiment, variance, probability) in result.items():
            # (sentiment, variance, probability, count)
            # sum here and divide by count after
            if category not in categories: categories[category] = [0, 0, 0, 0]
            categories[category][0] += sentiment
            categories[category][1] += variance
            categories[category][2] += probability
            categories[category][3] += 1
    for category in categories.keys():
        categories[category][0] /= float(categories[category][3])
        categories[category][1] /= float(categories[category][3])
        categories[category][2] /= float(school_totals[school][1])

    # average sentiment by confession
    average_sentiment = school_totals[school][0] / float(school_totals[school][1])

    print school
    print categories
    print average_sentiment
    print
