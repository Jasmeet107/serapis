# Serapis
Hierarchical sentiment analysis and categorization of college confessions, developed by Jasmeet Arora and Harry Rickards as a final proejct for MIT's [6.S083: Computation and Linguistics](https://www.eecs.mit.edu/academics-admissions/academic-information/subject-updates-ft-2015/6s083) class.

## Pipeline
For documentation on running each part of the pipeline, see the `README.md` files inside the individual directories for each pipeline part.

1. Scraping (`scraper`): downloads raw confessions data from Facebook
2. Parsing (`parser`): parse each confession into a syntactic tree
3. Tagging (`tagging`): use [Mechanical Turk](https://www.mturk.com/mturk/welcome) to create a tagged (by sentiment and topic) training dataset
4. Training (`training`): use classified learning to train a model to predict sentiment and topic
5. Evaluation (`evaluation`): run the trained model on all confessions in the corpus to predict sentiment and topic
6. Analysis (`analysis`): perform various statistical analyses across the evaluated dataset

## Setup
The following instructions should generalize to most Unix-like operating systems, but here were performed on Ubuntu Server 14.04 running on an Amazon EC2 `c4.large` instance.

The EC2 instance was launched with standard settings, with a security group making port 22 open for SSH. We use `serapis` as the hostname throughout the rest of this README, and suggest modifying `/etc/hosts` to make this work. The instance can then be SSH'ed into with

    ssh -i ".ssh/serapis.pem" ubuntu@serapis

The following core packages must then be installed

    sudo apt-get update
    sudo apt-get install build-essential git python-pip

### Installing Mongo
Add the MongoDB apt repository

    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
    echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list

Install the MongoDB server

    sudo apt-get update
    sudo apt-get install mongodb-org

This will automatically start mongo. Finally install the Python bindings

    sudo pip install pymongo
