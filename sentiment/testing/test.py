#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize, FreqDist, NaiveBayesClassifier
from nltk.tree import ParentedTree, Tree
from nltk.stem import SnowballStemmer
from pymongo import MongoClient
from bson.objectid import ObjectId
from progressbar import ProgressBar
from predict import SentimentPredictor
import subprocess, nltk, pickle
import csv

# db
client = MongoClient()
db = client.confessions

# read in mturk tagged sentences
num_sentences = 10
sentences = {}
with open("testing/data/sentences_tagged.csv", "rb") as resultsfile:
    for row in csv.DictReader(resultsfile):
        for i in range(1, num_sentences+1):
            parse_id = row["Input.confessionid_%d" % i]
            tree_id = int(row["Input.treeid_%d" % i])
            sentence_id = (parse_id, tree_id)
 
            sentiment = row["Answer.sentiment_%d" % i]
            if sentiment == "positive": sentiment = 1
            elif sentiment == "negative": sentiment = -1
            else: sentiment = 0

            if sentence_id not in sentences: sentences[sentence_id] = []
            sentences[sentence_id].append(sentiment)

# read in mturk tagged confessions
num_sentences = 10
confessions = {}
with open("testing/data/confessions_tagged.csv", "rb") as resultsfile:
    for row in csv.DictReader(resultsfile):
        for i in range(1, num_sentences+1):
            confession_id = row["Input.id_%d" % i]
 
            sentiment = row["Answer.sentiment_%d" % i]
            if sentiment == "positive": sentiment = 1
            elif sentiment == "negative": sentiment = -1
            else: sentiment = 0

            if confession_id not in confessions: confessions[confession_id] = []
            confessions[confession_id].append(sentiment)

def score_accuracy(data):
    accurate = 0
    inaccurate = 0
    for datum in data:
        if abs(datum["gold_sentiment"]) <= 0.5: continue
        s = datum["sentiment"]
        if datum["gold_sentiment"] < 0:
            if s < 0: accurate += 1
            else: inaccurate += 1
        else:
            if s > 0: accurate += 1
            else: inaccurate += 1
    return accurate*1.0/(accurate+inaccurate)

# predict sentence sentiments
predictor = SentimentPredictor()
for (parse_id, tree_id), sentiments in sentences.items():
    confession = db.parses.find_one({ "_id": ObjectId(parse_id) })
    tree = confession["trees"][tree_id]
    sentiment = sum(sentiments)*1.0/len(sentiments)
    predictor.add_tree({
        "raw_tree": tree,
        "gold_sentiment": sentiment
    })
predictor.run()
print score_accuracy(predictor.trees)

# predict confession sentiments
predictor = SentimentPredictor()
for parse_id, sentiments in confessions.items():
    confession = db.parses.find_one({ "_id": ObjectId(parse_id) })
    confession["gold_sentiment"] = sum(sentiments)*1.0/len(sentiments)
    predictor.add_confession(confession)
predictor.run()
print score_accuracy(predictor.confessions)
