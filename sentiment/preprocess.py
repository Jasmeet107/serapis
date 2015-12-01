#!/usr/bin/python
from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize
from nltk.tree import ParentedTree, Tree
from pymongo import MongoClient
from progressbar import ProgressBar

# db
client = MongoClient()
db = client.confessions

# vocab
vocab = set()

# find all parsed confessions
parses = db.parses.find(limit=100)
total = parses.count()
current_confession = 0
current_sentence = 0
with ProgressBar(max_value=total + 1) as progress, \
     open("parents.txt", "wb") as parents_file, \
     open("sents.txt", "wb") as sents_file:
    for confession in parses:
        # store sentence line numbers
        confession["sentences"] = []
        for raw_tree in confession["trees"]:
            if raw_tree == "None": continue
            # parse tree
            tree = Tree.fromstring(raw_tree)

            # binarize
            tree.chomsky_normal_form()
            tree.collapse_unary(collapsePOS=True)

            # make a parented tree
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
                if type(t[0]) is str or type(t[0]) is unicode:
                    labels.append(t[0])
                    vocab.add(t[0])

            parents_file.write(" ".join(map(str, parents)) + "\n")
            sents_file.write(" ".join(labels) + "\n")

            # store and increment sentence ID
            confession["sentences"].append(current_sentence)
            current_sentence += 1

        # save confession
        db.parses.save(confession)

        # update progress bar
        progress.update(current_confession)
        current_confession += 1

with open("vocab.txt", "wb") as vocab_file:
    for word in vocab:
        vocab_file.write(word + "\n")
