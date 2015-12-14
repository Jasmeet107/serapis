import pickle
from pymongo import MongoClient
import sentiment
from sentiment.predict import SentimentPredictor
import numpy as np
from nltk import Tree
from nltk.stem import SnowballStemmer
from bson.objectid import ObjectId

# db
client = MongoClient()
db = client.confessions

class Classifier:
    def __init__(self):
        # load classifiers
        all_categories = ["academics", "drugs", "housing", "mental_health", "politics", "relationships", "sex", "social", "sports"]
        self.classifiers = {}
        self.word_features = {}
        for category in all_categories:
            classifier_file = open("categorizer/classifiers/%s.pickle" % category, "rb")
            classifier = pickle.load(classifier_file)
            self.classifiers[category] = classifier["classifier"]
            self.word_features[category] = classifier["word_features"]
            classifier_file.close()

        # setup word stemmer
        self.stemmer = SnowballStemmer("english")

    def classify(self, tree):
        words = [self.stemmer.stem(word).lower() for word in tree.leaves()]
        categories = {}
        for category, classifier in self.classifiers.items():
            features = { feature: (feature in words) for feature in self.word_features[category] }
            prob = classifier.prob_classify(features).prob(category)
            categories[category] = prob
        return categories

classifier = Classifier()
predictor = SentimentPredictor()

ANALYZER_VERSION = 3

# iterate over confessions and predict categories and sentiment
confessions = db.parses.find({
    "analyzed": { "$ne": ANALYZER_VERSION }
}, limit=500)
threshold = 0.2
for confession in confessions:
    for tree_id, raw_tree in enumerate(confession["trees"]):
        if raw_tree == "None": continue

        # get sentence categories
        tree = Tree.fromstring(raw_tree)
        categories = [(category, prob) for (category, prob) in classifier.classify(tree).items() if prob > threshold]

        # add to queue to get sentence sentiment
        predictor.add_tree({
            "raw_tree": raw_tree,
            "tree_id": tree_id,
            "categories": categories,
            "confession_id": confession["_id"]
        })

# run sentiment predictor
predictor.run()

# aggregate by confession
confession_results = {}
for datum in predictor.trees:
    if datum["confession_id"] not in confession_results: confession_results[datum["confession_id"]] = []
    confession_results[datum["confession_id"]].append(datum)

for confession_id, sentences in confession_results.items():
    categories = {}
    probabilities = {}
    for sentence in sentences:
        for category, probability in sentence["categories"]:
            if category not in categories: categories[category] = []
            if category not in probabilities: probabilities[category] = []
            categories[category].append(sentence["sentiment"])
            probabilities[category].append(probability)

    N = len(sentences)
    results = { category: (np.mean(data), np.var(data), sum(probabilities[category])/N) for (category, data) in categories.items() }
    confession = db.parses.find_one({"_id": ObjectId(confession_id) })
    confession["analyzed"] = ANALYZER_VERSION
    db.parses.save(confession)
    datum = {
        "confession_id": confession_id,
        "sentiment": np.mean([sentence["sentiment"] for sentence in sentences]),
        "categories": results
    }
    db.results.insert(datum)
