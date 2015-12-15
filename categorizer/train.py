#i!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize, FreqDist, MaxentClassifier, NaiveBayesClassifier
from nltk.tree import ParentedTree, Tree
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from nltk.metrics import scores
from pymongo import MongoClient
from progressbar import ProgressBar
import subprocess, nltk, pickle
import itertools
import csv, random, re
from termcolor import colored
from sklearn.svm import LinearSVC
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.feature_extraction.text import TfidfTransformer

corpus = []

# remove confession numbers
fixer_regex = re.compile(r"^(#|Rhodes Confessions? )\d+:?\s+(.*)$", re.DOTALL)
def fix_sentence(s):
    if s[0] != "#" and s[:17] != "Rhodes Confession": return s
    m = fixer_regex.match(s)
    if m != None: return m.groups()[1]
    return s

# preprocess sentence
stemmer = SnowballStemmer("english")
all_stopwords = stopwords.words("english")
def preprocess(sentence):
    # tokenize into words
    words = [unicode(word.lower()) for word in word_tokenize(fix_sentence(sentence))]
    # remove stopwords
    words = [word for word in words if word not in all_stopwords]
    # stem words
    words = map(stemmer.stem, words)
    return words

# read in mturk tagged sentences
# with open("results.csv", "rb") as resultsfile:
    # reader = csv.DictReader(resultsfile)
    # for row in reader:
        # num_sentences = 5
        # for i in range(1, num_sentences+1):
            # sentence = preprocess(row["Input.sentence%d" % i])
            # categories = [c for c in row["Answer.sentence%d" % i].split("|") if len(c) > 0]
            # corpus.append((sentence, categories))

# read in human tagged data
with open("data.csv", "rb") as humanfile:
    reader = csv.reader(humanfile)
    for row in reader:
        sentence = preprocess(row[0])
        categories = [c.strip() for c in row[1].split(",") if len(c) > 0]
        corpus.append((sentence, categories))

# extract features
def features(words):
    features = {}
    for word in word_features:
        # features[word] = (word in words)
        features[word] = words.count(word)
    return features

# extract all possible categories
all_categories = set()
for (word, categories) in corpus:
    for category in categories: all_categories.add(category)

# train classifier for each category
f1_scores = []
accuracies = []
for category in all_categories:
    # label words
    def labelize(present):
        if present: return category
        else: return "no"

    # split our corpus into 50% category, 50% no data
    # for purposes of finding most common words
    new_size_corpus = len([words for (words, categories) in corpus if category in categories])
    if (len(corpus) - new_size_corpus < new_size_corpus): new_size_corpus = len(corpus) - new_size_corpus
    words_size = int(0.5*new_size_corpus)
    category_words = list(itertools.islice(((words, categories) for (words, categories) in corpus if category in categories), words_size))
    noncategory_words = list(itertools.islice(((words, categories) for (words, categories) in corpus if category not in categories), words_size))
    category_corpus = category_words + noncategory_words

    # find dictionary of most common words
    word_dist = FreqDist()
    for (words, categories) in category_corpus:
        for word in words: word_dist[word] += 1
    word_features = list(word_dist)[:1000]

    train_corpus = corpus[150:]
    test_corpus = corpus[:150]
    train_set = [(features(words), labelize(category in categories)) for (words, categories) in train_corpus]
    test_set = [(features(words), labelize(category in categories)) for (words, categories) in test_corpus]

    # train classifier
    # print "Training classifier for '%s'" % category
    # classifier = MaxentClassifier.train(train_set, max_iter= 3)
    # classifier = NaiveBayesClassifier.train(train_set)
    model = MultinomialNB()
    classifier = SklearnClassifier(model)

    # set priors
    classifier._encoder.fit([category, "no"])
    # [category, "no"] unless this is true then ["no", category]
    flip = classifier.labels()[0] == "no"
    categorized_proportion = len([words for (words, categories) in corpus if category in categories]) * 1.0 / len(corpus)
    if flip:
        model.class_prior = [1-categorized_proportion, categorized_proportion]
    else:
        model.class_prior = [categorized_proportion, 1-categorized_proportion]

    classifier.train(train_set)

    # test classifier
    test_results = classifier.classify_many([feat for (feat, label) in test_set])
    pos_test_set = set(i for i, result in enumerate(test_results) if result == category)
    reference_values = [label for (feat, label) in test_set]
    pos_ref_set = set(i for i, (feat, label) in enumerate(test_set) if label == category)
    accuracy = scores.accuracy(reference_values, test_results)
    accuracies.append(accuracy)
    precision = scores.precision(pos_ref_set, pos_test_set)
    recall = scores.recall(pos_ref_set, pos_test_set)
    f1 = scores.f_measure(pos_ref_set, pos_test_set)
    f1_scores.append(f1)

    print "%s: accuracy %s, precision %s, recall %s, F1 %s" % (colored(category, "blue"), colored(accuracy, "yellow"), colored(precision, "yellow"), colored(recall, "yellow"), colored(f1, "yellow"))
    ## print(nltk.classify.accuracy(classifier, test_set))
    # classifier.show_most_informative_features(5)
    # print ""

    # save trained classifier and word features to file
    dump_file = open("classifiers/%s.pickle" % category, "wb")
    pickle.dump({
        "classifier": classifier,
        "word_features": word_features
    }, dump_file)
    dump_file.close()

print "Average accuracy: %s" % colored(sum(accuracies)*1.0/len(accuracies), "red")
print "Average F1 score: %s" % colored(sum(f1_scores)*1.0/len(f1_scores), "red")
