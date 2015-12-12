#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize, FreqDist, NaiveBayesClassifier
from nltk.tree import ParentedTree, Tree
from nltk.stem import SnowballStemmer
from pymongo import MongoClient
from bson.objectid import ObjectId
from progressbar import ProgressBar
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
            sentence_id = (row["Input.confessionid_%d" %i], row["Input.treeid_%d" % i])
 
            sentiment = row["Answer.sentiment_%d" % i]
            if sentiment == "positive": sentiment = 1
            elif sentiment == "negative": sentiment = -1
            else: sentiment = 0

            if sentence_id not in sentences: sentences[sentence_id] = []
            sentences[sentence_id].append(sentiment)

# read in mturk tagged confessions
num_confessions = 10
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

def score_accuracy(items, metric):
    accurate = 0
    inaccurate = 0
    for key, sentiments in items.items():
        # all the same
        if len(set(sentiments)) == 1:
            accurate += 1
        elif len(set(sentiments)) == 2:
            sset = list(set(sentiments))
            c1 = len([s for s in sentiments if s == sset[0]])
            c2 = len([s for s in sentiments if s == sset[1]])
            if c1 == 3 or c2 == 3:
                accurate += 1
            elif 0 in sset:
                if metric == 0:
                    accurate += 1
                elif metric == 1:
                    inaccurate += 1
            else:
                inaccurate += 1
        else:
            inaccurate += 1
    return accurate*1.0/(accurate + inaccurate)

# 3 different accuracy metrics
for i in range(3):
    print "Accuracy metric %d" % (i+1)
    print "Sentences: %.5f" % score_accuracy(sentences, i)
    print "Confessions: %.5f" % score_accuracy(confessions, i)
    print
