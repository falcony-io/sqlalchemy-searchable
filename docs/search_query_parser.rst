Search query parser
===================

As of version 0.3.0 SQLAlchemy-Searchable comes with built in search query parser. The search query parser is capable of parsing human readable search queries into PostgreSQL search query syntax.



AND operator
------------

Example: Search for articles containing 'star' and 'wars'

The default operator is 'and', hence the following queries are essentially the same:

::

    query = search(query, 'star wars')
    query2 = search(query, 'star and wars')
    assert query == query2

OR operator
------------

Searching for articles containing 'star' or 'wars'

::


    query = search(query, 'star or wars')


Negation operator
-----------------

SQLAlchemy-Searchable search query parser supports negation operator. By default the negation operator is '-'.

Example: Searching for article containing 'star' but not 'wars'

::


    query = search(query, 'star or -wars')



Parenthesis
-----------

1. Searching for articles containing 'star' and 'wars' or 'luke'

::


    query = search(query '(star wars) or luke')



Special cases
-------------


Hyphens between words
^^^^^^^^^^^^^^^^^^^^^

SQLAlchemy-Searchable is smart enough to not convert hyphens between words to negation operators. Instead, it simply converts all hyphens between words to spaces.

Hence the following search queries are essentially the same:

::


    query = search(query, 'star wars')
    query2 = search(query, 'star-wars')


Emails as search terms
^^^^^^^^^^^^^^^^^^^^^^

PostgreSQL tsvectors handle email strings in a way that they don't get split into multiple tsvector terms. SQLAlchemy-Searchable handles email search terms the same way:

::

    # single search term used: 'john@fastmonkeys.com'
    query = search(query, u'john@fastmonkeys.com')

    # not a valid email, split into three search terms:
    # 'john', 'fastmonkeys' and 'com'
    query = search(query, u'john@@fastmonkeys.com')


Internals
---------

If you wish to use only the query parser this can be achieved by invoking `parse_search_query` function. This function parses human readable search query into PostgreSQL specific format.

::


    parse_search_query('(star wars) or luke')
    # (star:* & wars:*) | luke:*
