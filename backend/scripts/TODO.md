# __To do__
+ in site_words instead of duplicate word occurrences, add a count column so site_words will be site id | word id | count
+ for search there could be huge optimization
  + right now I search thorugh db for each keyword and then find intersection.
    this lowkey cringe. I should search filter for a word and then each keyword after is a filter for the previous set
    + if i'm feeling fancy I could even prioritize words with the most occurences so that you narrow down faster and faster
+ update the search function to new stuff

# __Done__
+ holy freak I deleted the new script for search with multiple keyword
  i wasn't that far into it but still grrrr
+ add multi keyword search
+ work on parallelization and multiple crawlers
+ + deque and async is most optimal maybe
 the search time is way too slow. for ~600 sites
  I'm using upwards of 11 seconds of cpu time for ONE WORD
  I need to switch to word id | site id instead of word string | site id
+ i need to switch to postgresql ELSIFHSOEUBHF:OSUEBHGF:OSEHGo
+ rewrite and stop using recursion for crawling its bad
+ optimize insertion in keyword index database
