import pymongo
import csv
import random
import re
from nltk import sent_tokenize

# db
client = pymongo.MongoClient()
db = client.confessions

# iterate over each confession in random order
parses = list(db.parses.find())
random.shuffle(parses)

fixer_regex = re.compile(r"^(#|Rhodes Confession )\d+:?\s+(.*)$")
def fix_sentence(s):
    if s[0] != "#" and s[:17] != "Rhodes Confession": return s
    m = fixer_regex.match(s)
    if m != None: return m.groups()[1]
    return s

senti = []

# take first n sentences
for confession in parses[:1665]:
    sentences = sent_tokenize(confession["message"])
    sentences = filter(lambda s: len(s.strip()) > 0, sentences)
    sentence = fix_sentence(sentences[random.randint(0, len(sentences)-1)])
    sentence = sentence.encode("ascii", errors="ignore")
    senti.append(sentence)

# write out to csv
with open("sentences.csv", "wb") as sent_file:
    writer = csv.writer(sent_file)
    writer.writerow(['sentence1', 'sentence2', 'sentence3', 'sentence4', 'sentence5'])
    for i in range(len(senti) / 5):
        writer.writerow([senti[5*i], senti[5*i+1], senti[5*i+2], senti[5*i+3], senti[5*i+4]])
