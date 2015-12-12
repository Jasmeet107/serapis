import pymongo
import csv
import random
import re
from nltk import sent_tokenize, Tree

# db
client = pymongo.MongoClient()
db = client.confessions

# iterate over each confession in random order
parses = list(db.parses.find())
random.shuffle(parses)

texts = []

# take first n confessions
for confession in parses[:1000]:
    treeid = random.randint(0, len(confession["trees"])-1)
    raw_tree = confession["trees"][treeid]
    tree = Tree.fromstring(raw_tree)
    texts.append((confession["_id"], treeid, " ".join(tree.leaves())))

# write out to csv
num_texts = 10
with open("data/sentences.csv", "wb") as texts_file:
    writer = csv.writer(texts_file)
    header = []
    for i in range(1, num_texts+1):
        header.append("confessionid_%d" % i)
        header.append("treeid_%d" % i)
        header.append("text_%d" % i)
    writer.writerow(header)
    for i in range(len(texts) / num_texts):
        row = []
        for j in range(num_texts):
            datum = texts[num_texts*i+j]
            row.append(datum[0])
            row.append(datum[1])
            row.append(datum[2])
        writer.writerow(row)
