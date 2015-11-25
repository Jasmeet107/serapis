# Stage 1: Parser
This stage of the pipeline uses the Facebook Graph API to download confessions from a number of colleges with popular confessions pages (currently Brown University, University of Wisconsin-Madison, Stanford University, Rhodes College, Boston University, and MIT). These confessions are then stored in the `confessions` collection in mongo (db `confessions`).

## Setup
A Facebook *app* is needed to create an OAuth access token that can be used to authenticate with the Graph API. Create one at [developers.facebook.com](https://developers.facebook.com/apps/) and note the App ID and App Secret. Place these into the configuration file `config.py` (you may need to `cp config.py.example config.py`).

Install the required python packages with

	sudo pip install facebook-sdk requests_cache

## Running
Run

	python confessions.py

This may take a while, but the script will provide output detailing its progress as it runs. If the script fails (likely due to hitting a rate-limit in the graph API) just rerun it: it caches previously-scraped confessions.
