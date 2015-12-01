#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize
from nltk.tree import ParentedTree, Tree
from pymongo import MongoClient
from progressbar import ProgressBar
import subprocess

class SentimentPredictor():
    def __init__(self):
        # line number counter
        self.current_sentence = 0
        # confessions processed
        self.confessions = []
        self.predictions = []

        # files to write output
        self.parents_file = open("parents.txt", "wb")
        self.sents_file = open("sents.txt", "wb")


    def add(self, confession):
        # store line numbers
        confession["sentences"] = []

        # analyze each sentence seperately
        for raw_tree in confession["trees"]:
            if raw_tree == "None": continue
            # parse tree and binarize
            tree = Tree.fromstring(raw_tree)
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

            # store and increment sentence ID
            confession["sentences"].append(self.current_sentence)
            self.current_sentence += 1

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
            # 3 = positive, 1 = negative
            # ---> 1 = positive, -1 = negative
            self.predictions = [float(line.strip()) - 2 for line in predictions_file.readlines()]
        for i, confession in enumerate(self.confessions):
            confession["sentiments"] = [self.predictions[sentence] for sentence in confession["sentences"]]
            self.confessions[i] = confession

if __name__ == "__main__":
    # db
    client = MongoClient()
    db = client.confessions

    # find all parsed confessions
    parses = db.parses.find(limit=100)
    total = parses.count()
    current_confession = 0
    predictor = SentimentPredictor()
    with ProgressBar(max_value=total + 1) as progress:
        for confession in parses:
            # preprocess
            predictor.add(confession)

            # update progress bar
            # progress.update(current_confession)
            current_confession += 1

    # predict
    predictor.run()

    # print output
    for confession in predictor.confessions:
        for tree, prediction in zip(confession["trees"], confession["sentiments"]):
            print " ".join(Tree.fromstring(tree).leaves())
            print prediction
            print
