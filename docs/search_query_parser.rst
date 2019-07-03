Search query parser
===================

As of version 1.0 SQLAlchemy-Searchable comes with native PostgreSQL search query parser. The search query parser is capable of parsing human readable search queries into PostgreSQL search query syntax.


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


    query = search(query, '(star wars) or luke')


Phrase searching
----------------

SQLAlchemy-Searchable supports phrase searches. Just add the keywords in double quotes.::


query = search(query, '"star wars"')



Internals
---------

If you wish to use only the query parser this can be achieved by invoking `parse` function. This function parses human readable search query into PostgreSQL tsquery format.

::


    session.execute("SELECT tsq_parse('(star wars) or luke')").scalar()
    # (star:* & wars:*) | luke:*
