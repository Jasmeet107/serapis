#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize, FreqDist, NaiveBayesClassifier
from nltk.tree import ParentedTree, Tree
from nltk.stem import SnowballStemmer
from pymongo import MongoClient
from progressbar import ProgressBar
import subprocess, nltk, pickle
import csv

corpus = []

# preprocess sentence
stemmer = SnowballStemmer("english")
def preprocess(sentence):
    # tokenize into words
    words = [stemmer.stem(word).lower() for word in word_tokenize(sentence)]
    return words

# read in mturk tagged sentences
with open("results.csv", "rb") as resultsfile:
    reader = csv.DictReader(resultsfile)
    for row in reader:
        num_sentences = 5
        for i in range(1, num_sentences+1):
            sentence = preprocess(row["Input.sentence%d" % i])
            categories = [c for c in row["Answer.sentence%d" % i].split("|") if len(c) > 0]
            corpus.append((sentence, categories))

# find dictionary of most common words
word_dist = FreqDist()
for (words, categories) in corpus:
    for word in words: word_dist[word] += 1
word_features = list(word_dist)[:2000]
features_file = open("classifiers/features.pickle", "wb")
pickle.dump(word_features, features_file)
features_file.close()

# extract features
def features(words):
    features = {}
    for word in word_features:
        features[word] = (word in words)
    return features

# extract all possible categories
all_categories = set()
for (word, categories) in corpus:
    for category in categories: all_categories.add(category)

# train classifier for each category
for category in all_categories:
    # label words
    def labelize(present):
        if present: return category
        else: return "no"
    dataset = [(features(words), labelize(category in categories)) for (words, categories) in corpus]
    train_set, test_set = dataset[100:], dataset[:100]

    # train classifier
    print "Training classifier for '%s'" % category
    classifier = NaiveBayesClassifier.train(train_set)
    print(nltk.classify.accuracy(classifier, test_set))
    classifier.show_most_informative_features(5)
    print ""

    # save trained classifier to file
    dump_file = open("classifiers/%s.pickle" % category, "wb")
    pickle.dump(classifier, dump_file)
    dump_file.close()
