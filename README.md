Hello (^-^)/

# Intro
NeoSearch is a search engine for Neocities.org, a site that hosts a static site for you for free!
It's an incredible service, and I tell everyone on and offline to make a website through it. In addition to hosting static sites, it also has accompanying profiles on its own website that allow you to follow others, watch for updates, and comment and send them messages.
Unfortunately, Neocities lacks a search function that would help people find websites they love, and as
many rabbitholes as there are through beautifully, handcrafted websites, not knowing where to start makes it harder to jump down them.

NeoSearch aims to make Neocities more accessible for both experienced and inexperienced IndieWeb surfers by showing them websites relevant to them and gives them entrances into the vast interconnected rabbit holes that make up the IndieWeb.

It uses a concept vaguely based on pageRank by Google, but it uses Neocities analytics in addition to links between sites. It transforms an intermittently indexed large list of interconnected websites through Neocities social functions, and content contained on the websites themselves.

The backend of NeoSearch is written in python with scraping done with the library [Scrapy](https://www.scrapy.org/) and databases written in SQL/sqlite3, although this is likely to change to PostgreSQL in the future.

Currently NeoSearch indexes approximately 31,000 websites. Despite Neocities having many, many more sites than this (over 1.3 million according to the landing page), this seems to be the extent of the currently active and socially connected websites unless there are communities that share absolutely no connections to the main social graph.

# Current Features
NeoSearch currently supports exact multi keyword searching with plans for semantic search in the future.

# Installation
NeoSearch is built with Python 3.13.

The dependencies required for the python scripts to run can be found in requirements.txt

Installing these should preferably be done in a [virtual environment](https://docs.python.org/3/library/venv.html), but they can also just be installed globally.

To install these, simply run this scripts in bash(linux) or zsh (macOS) when in the venv or just from the terminal if you are installing globally

```
pip install -r requirements.txt	
```

A small database of 500 websites is included in the repo, but if you would like to index your own, simply run this command. Each of these commands is likely to take a while. A progress bar is included in the console.

## zsh (macOS)
```
python3 scripts/init_crawler.py "the number of sites you want to crawl"
```

## bash (linux)
```
python scripts/init_crawler.py "the number of sites you want to crawl"
```

Upon its completion run this command to build the database for words from websites

## zsh (macOS)
```
python3 scripts/word_indexer.py
```

## bash (linux)
```
python scripts/word_indexer.py
```

Then run this command to create the database for the rankings of sites that is used to rank results
## zsh (macOS)
```
python3 scripts/neoranker.py
```

## bash (linux)
```
python scripts/neoranker.py
```

This should make your own local database.

# Usage

To search something just run
```
python3 scripts/search.py "keywords you want to search"
```

It will output all the relevant sites in their ranked order.

# Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
