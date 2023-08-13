Search query parser
===================

SQLAlchemy-Searchable includes a search query parser that enables the conversion
of human-readable search queries into PostgreSQL search query syntax.

AND operator
------------

The search query parser treats search terms as if they are connected with an
implied AND operator. To search for articles containing both "star" and "wars",
simply use the query "star wars"::

    query = search(query, 'star wars')

OR operator
------------

The OR operator in the search query parser allows you to broaden your search to
include results that contain any of the specified terms. To search for articles
containing either "star" or "wars", you can utilize the OR operator as follows::

    query = search(query, 'star or wars')

Negation operator
-----------------

Th search query parser supports excluding words from the search. Enter ``-`` in
front of the word you want to leave out. To search for articles containing
"star" but not "wars", you can use the query "star -wars"::

    query = search(query, 'star -wars')

Phrase searching
----------------

If you need to search for a specific phrase, enclose the phrase in double quotes::

    query = search(query, '"star wars"')

Internals
---------

If you wish to use only the query parser, this can be achieved by invoking the
``parse_websearch`` function. This function parses human readable search query into
PostgreSQL ``tsquery`` format::

    >>> session.execute("SELECT parse_websearch('(star wars) or luke')").scalar()
    '(star:* & wars:*) | luke:*'
