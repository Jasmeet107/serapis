import pymongo
import csv
import random
import re
from nltk import sent_tokenize
from termcolor import colored

# db
client = pymongo.MongoClient()
db = client.confessions

# iterate over each confession in random order
parses = list(db.parses.find())
random.shuffle(parses)

fixer_regex = re.compile(r"^(#|Rhodes Confessions? )\d+:?\s+(.*)$", re.DOTALL)
def fix_sentence(s):
    if s[0] != "#" and s[:17] != "Rhodes Confession": return s
    m = fixer_regex.match(s)
    if m != None: return m.groups()[1]
    return s

senti = []

# take first n sentences
filename = raw_input("Filename: ")
with open(filename, "wb") as f:
    writer = csv.writer(f)
    for confession in parses:
        sentences = sent_tokenize(confession["message"])
        sentences = filter(lambda s: len(s.strip()) > 0, sentences)
        sentence = fix_sentence(sentences[random.randint(0, len(sentences)-1)])
        sentence = sentence.encode("ascii", errors="ignore")

        print colored(sentence, "blue")
        category_mappings = {"d": "drugs", "x": "sex", "a": "academics", "s": "social", "r": "relationships", "p": "politics", "m": "mental_health", "h": "housing", "o": "sports"}
        instructions = []
        for shortcut, category in category_mappings.items():
            instructions.append("%s for %s" % (colored(shortcut, "cyan"), colored(category, "yellow")))
        print "Instructions: %s" % ", ".join(instructions)

        categories = list(raw_input("Categories? ").strip())
        writer.writerow([sentence, ",".join([category_mappings[category] for category in categories])])
        print "Classified as %s" % ", ".join([colored(category_mappings[category], "red") for category in categories])
        print
