# Stage 2: Parser
The second stage of the pipeline parses the raw text of each confession into a syntactic tree. Each confession is tokenized into sentences and words using NLTK's punkt tokenizer, and then fed into the BLLIP reranking parser (a state-of-the-art parser referred to as a Charniak parser in the literature). Parse trees for each sentence are then stored in the `parses` collection in mongo (`confessions` db).

## Setup
### Installing BLLIP Parser
   Download BLLIP
   
    git clone https://github.com/BLLIP/bllip-parser.git
    cd bllip-parser

First install prerequisites

    sudo apt-get install flex swig python-dev
    
and then build and install BLLIP

    make

and the python bindings

    python setup.py build
    sudo python setup.py install

### Installing NLTK
Run

    sudo pip install nltk

And download the required datasets with

    python -m nltk.downloader punkt

### Installing Other Python Depednencies
Run

    sudo pip install progressbar2

## Running
Run

    python parse.py

Parsing all confessions in the corpus will take a long time, but the parser can be stopped and started at will without reparsing any confessions (to cause a confession to be reparsed, increment `PARSER_VERSION` at the top of `parse.py`).
