Hello (^-^)/

# Intro
NeoSearch is a search engine for Neocities.org, a site that hosts a static site for you for free!
It's an incredible service, and I tell everyone on and offline to make a website through it. In addition to hosting static sites, it also has accompanying profiles on its own website that allow you to follow others, watch for updates, and comment and send them messages.
Unfortunately, Neocities lacks a search function that would help people find websites they love, and as
many rabbitholes as there are through beautifully, handcrafted websites, not knowing where to start makes it harder to jump down them.

NeoSearch aims to make Neocities more accessible for both experienced and inexperienced IndieWeb surfers by showing them websites relevant to them and gives them entrances into the vast interconnected rabbit holes that make up the IndieWeb.

It uses a concept vaguely based on pageRank by Google, but it uses Neocities analytics in addition to links between sites. It transforms an intermittently indexed large list of interconnected websites through Neocities social functions, and content contained on the websites themselves.

The backend of NeoSearch is written in python with scraping done with the library [Scrapy](https://www.scrapy.org/) and databases written in SQL/sqlite3.

# Current Features
NeoSearch currently supports exact multi keyword searching with plans for semantic search in the future.

# Installation
NeoSearch is built with Python 3.13.

All the files related to the frontend of the website can be found in the frontend directory
This includes the HTML, CSS, and Javascript.

For the backend:

The dependencies required for the python scripts to run can be found in backend/requirements.txt

Installing these should preferably be done in a [virtual environment](https://docs.python.org/3/library/venv.html), but they can also just be installed globally.

To install these, simply run this scripts in Linux or macOS when in the venv or just from the terminal if you are installing globally

```
pip install -r requirements.txt	
```

A small database of 500 websites is included in the repo, but if you would like to index your own, simply run this command. Each of these commands is likely to take a while. A progress bar is included in the console.

## macOS/Linux
```
python3 scripts/init_crawler.py "name of starting profile" "the number of sites you want to crawl"
python3 scripts/word_indexer.py
python3 scripts/tf-idf.py
```

## Linux
```
python scripts/init_crawler.py "the number of sites you want to crawl"
python scripts/word_indexer.py
```

Upon its completion run this command to build the database for words from websites

Then run this command to create the database for the rankings of sites that is used to rank results
## macOS
```
python3 scripts/neoranker.py
```

## Linux
```
python scripts/neoranker.py
```

This should make your own local database.

# Usage

To search something in the UI just run
```
python3 scripts/search.py "keywords you want to search"
```

It will output all the relevant sites in their ranked order.

For dev purposes it is also possible to start a flask server to make requests to a locally served flask server.
To do so run this command
```
flask --app /backend/app.py run
```

# Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
