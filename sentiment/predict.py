#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize
from nltk.tree import ParentedTree, Tree
from pymongo import MongoClient
from progressbar import ProgressBar
import numpy as np
import subprocess

class SentimentPredictor():
    def __init__(self):
        # confessions processed
        self.confessions = []
        self.trees = []
        self.predictions = []

        # files to write output
        self.parents_file = open("parents.txt", "wb")
        self.sents_file = open("sents.txt", "wb")

    def add_tree(self, datum):
        # parse tree and binarize
        tree = Tree.fromstring(datum["raw_tree"])
        tree.chomsky_normal_form()
        tree.collapse_unary(collapsePOS=True)
        tree = ParentedTree.convert(tree)

        # assign indices to subtrees
        indices = {}
        counter = 0
        for t in tree.subtrees():
            indices[t.treeposition()] = counter
            counter += 1

        # generate parent pointers and labels
        # (labels = one instance of sent in sents by treelstm terminology)
        parents = [0] * (counter - 1)
        labels = []
        counter = 0
        for t in tree.subtrees():
            parent = t.parent()
            if parent != None:
                parents[counter] = indices[parent.treeposition()]
                counter += 1
            if type(t[0]) is str or type(t[0]) is unicode: labels.append(t[0])

        self.parents_file.write(" ".join(map(str, parents)) + "\n")
        self.sents_file.write(" ".join(labels) + "\n")
        self.trees.append(datum)
        return len(self.trees) - 1 # ID

    def add_confession(self, confession):
        # store line numbers
        confession["tree_ids"] = []

        # analyze each sentence seperately
        for raw_tree in confession["trees"]:
            if raw_tree == "None": continue
            confession["tree_ids"].append(self.add_tree({
                "raw_tree": raw_tree
            }))

        # store confession
        self.confessions.append(confession)

    # call lua predictor script
    def run(self):
        self.parents_file.close()
        self.sents_file.close()

        # run lua cli script
        subprocess.call(["th", "run.lua"], cwd="../treelstm")

        # open predictions, and assign to confessions
        with open("predictions.txt", "rb") as predictions_file:
            # 1 = negative prob, 2 = neutral prob, 3 = positive prob
            self.predictions = []
            self.expected_values = []
            for line in predictions_file:
                predictions = map(float, line.split(",")[:3])
                # convert from log likelihood
                predictions = map(np.exp, predictions)
                self.predictions.append(predictions[2] - predictions[0])

        for i, datum in enumerate(self.trees):
            datum["sentiment"] = self.predictions[i]

        for i, confession in enumerate(self.confessions):
            confession["sentiments"] = [self.predictions[tree_id] for tree_id in confession["tree_ids"]]
            confession["sentiment"] = sum(confession["sentiments"])*len(confession["sentiments"])
            self.confessions[i] = confession

if __name__ == "__main__":
    # db
    client = MongoClient()
    db = client.confessions

    # find all parsed confessions
    parses = db.parses.find(limit=1)
    total = parses.count()
    current_confession = 0
    predictor = SentimentPredictor()
    with ProgressBar(max_value=total + 1) as progress:
        for confession in parses:
            # preprocess
            predictor.add_confession(confession)

            # update progress bar
            # progress.update(current_confession)
            current_confession += 1

    # predict
    predictor.run()

    # print output
    for confession in predictor.confessions:
        print confession["message"]
        print confession["sentiment"]
