from nltk.parse.bllip import BllipParser
from bllipparser.ModelFetcher import download_and_install_model
from nltk import word_tokenize, sent_tokenize
from pymongo import MongoClient
from progressbar import ProgressBar

# version parsing logic so we don't unnecessarily reparse confessions
PARSER_VERSION = 1

# download SANCL2012-Uniform (trained on WSJ Portion of OntoNotes
# and Google Web Treebank) model if not already present
model_dir = download_and_install_model('SANCL2012-Uniform')

# load model (slow)
print "Loading model (this may take a few minutes)..."
bllip = BllipParser.from_unified_model_dir(model_dir)

# db
client = MongoClient()
db = client.confessions
db.parses.drop()

# find all raw confessions not already parsed (by this version of the parser)
confessions = db.confessions.find({
    "parsed": { "$ne": PARSER_VERSION }
})
total = confessions.count()
current = 0
with ProgressBar(max_value=total) as progress:
    for confession in confessions:
        # tokenize confession post into sentences using pretained NLTK punkt tokenizer
        sentences = sent_tokenize(confession["message"])
        trees = [] # one tree per sentence
        for sentence in sentences:
            # then tokenize each sentence into words also using the punkt tonizer
            words = word_tokenize(sentence)
        
            # bllip doesn't support non-ASCII chars: as we're just looking at english
            # language data, we filter out all non-ASCII chars
            words = map(lambda w: w.encode("ascii", errors="ignore"), words)
            words = filter(lambda w: len(w) > 0, words)
            if len(words) == 0: continue

            # use bllip 1-best to parse into most likely tree
            tree = bllip.parse_one(words)

            # store string representation of tree (can be parsed using Tree.fromstring)
            trees.append(str(tree))

        # store parse in mongo
        parse = {
            "message": confession["message"],
            "school": confession["school"],
            "trees": trees,
            "confession_id": confession["id"]
        }
        db.parses.insert_one(parse)

        # update confession to reflect it's been parsed
        confession["parsed"] = PARSER_VERSION
        db.confessions.save(confession)

        # update progress bar
        progress.update(current)
        current += 1
