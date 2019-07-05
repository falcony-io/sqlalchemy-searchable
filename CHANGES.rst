Changelog
---------

Here you can see the full list of changes between each SQLAlchemy-Searchable release.


1.1.0 (2019-07-05)
^^^^^^^^^^^^^^^^^^

- Fixed some issues with query parsing
- Fixed 'or' keyword parsing (#85)
- Dropped py33 support
- Fixed deprecation warnings (#81, pull request courtesy of Le-Stagiaire)


1.0.3 (2018-02-22)
^^^^^^^^^^^^^^^^^^

- Add missing expressions.sql


1.0.2 (2018-02-22)
^^^^^^^^^^^^^^^^^^

- Fixed import issue with expressions.sql


1.0.1 (2018-02-20)
^^^^^^^^^^^^^^^^^^

- Made all parser functions immutable


1.0 (2018-02-20)
^^^^^^^^^^^^^^^^

- Added pure PostgreSQL search query parsing (faster and can be used on SQL level)
- PostgreSQL >= 9.6 required
- Added support for phrase searching
- Removed python search query parsing
- Removed pyparsing from requirements
- Removed symbol removal (now handled implicitly on PostgreSQL side)


0.10.6 (2017-10-12)
^^^^^^^^^^^^^^^^^^^

- Fixed Flask-SQLAlchemy support (#63, pull request by quantus)


0.10.5 (2017-07-25)
^^^^^^^^^^^^^^^^^^^

- Added drop_trigger utility function (#58, pull request by ilya-chistyakov)


0.10.4 (2017-06-28)
^^^^^^^^^^^^^^^^^^^

- Index generation no longer manipulates table args (#55, pull request by jmuhlich)


0.10.3 (2017-01-26)
^^^^^^^^^^^^^^^^^^^

- Fixed 'Lo' unicode letter parsing (#50, pull request courtesy by StdCarrot)


0.10.2 (2016-09-02)
^^^^^^^^^^^^^^^^^^^

- Fixed vector matching to use global configuration regconfig as fallback


0.10.1 (2016-04-14)
^^^^^^^^^^^^^^^^^^^

- Use identifier quoting for reserved keywords (#45, pull request by cristen)


0.10.0 (2016-03-31)
^^^^^^^^^^^^^^^^^^

- Fixed unicode parsing in search query parser, #42
- Removed Python 2.6 support


0.9.3 (2015-05-31)
^^^^^^^^^^^^^^^^^^

- Added support for search term weights


0.9.2 (2015-04-01)
^^^^^^^^^^^^^^^^^^

- Fixed listener configuration (#31)


0.9.1 (2015-03-25)
^^^^^^^^^^^^^^^^^^

- Added sort param to search function for ordering search results by relevance


0.9.0 (2015-03-19)
^^^^^^^^^^^^^^^^^^

- Added PyPy support
- Added isort and flake8 checks
- Added support for custom vectorizers in sync_trigger, #25
- Fixed and / or parsing where search word started with keyword, #22
- Removed 'and' as keyword from search query parser (spaces are always considered as 'and' keywords)


0.8.0 (2015-01-03)
^^^^^^^^^^^^^^^^^^

- Made search function support for queries without entity_zero
- Changed catalog configuration option name to regconfig to be compatible with the PostgreSQL and SQLAlchemy naming
- Added custom type and column vectorizers
- SQLAlchemy requirement updated to 0.9.0
- SQLAlchemy-Utils requirement updated to 0.29.0


0.7.1 (2014-12-16)
^^^^^^^^^^^^^^^^^^

- Changed GIN indexes to table args Index constructs. This means current version of alembic should be able to create these indexes automatically.
- Changed GIN index naming to adhere to SQLAlchemy index naming conventions


0.7.0 (2014-11-17)
^^^^^^^^^^^^^^^^^^

- Replaced remove_hyphens configuration option by more generic remove_symbols configuration option
- Emails are no longer considered as special tokens by default.


0.6.0 (2014-09-21)
^^^^^^^^^^^^^^^^^^

- Added sync_trigger alembic helper function


0.5.0 (2014-03-19)
^^^^^^^^^^^^^^^^^^

- Python 3 support
- Enhanced email token handling
- New configuration option: remove_hyphens


0.4.5 (2013-10-22)
^^^^^^^^^^^^^^^^^^

- Updated validators dependency to 0.2.0


0.4.4 (2013-10-17)
^^^^^^^^^^^^^^^^^^

- Search query string parser now notices emails and leaves them as they are (same behavious as in PostgreSQL tsvector parser)


0.4.3 (2013-10-07)
^^^^^^^^^^^^^^^^^^

- Fixed index/trigger creation when multiple vectors attached to single class
- Search vector without columns do not generate triggers anymore


0.4.2 (2013-10-07)
^^^^^^^^^^^^^^^^^^

- Fixed single table inheritance handling in define_triggers_and_indexes manager method.


0.4.1 (2013-10-04)
^^^^^^^^^^^^^^^^^^

- Fixed negation operator parsing


0.4.0 (2013-10-04)
^^^^^^^^^^^^^^^^^^

- Completely rewritten search API
- Renamed SearchQueryMixin.search and main module search function's 'language' parameter to 'catalog'
- Support for multiple search vectors per class


0.3.3 (2013-10-03)
^^^^^^^^^^^^^^^^^^

- Fixed support for numbers in parse_search_query


0.3.2 (2013-10-03)
^^^^^^^^^^^^^^^^^^

- Added support for hyphens between words


0.3.1 (2013-10-02)
^^^^^^^^^^^^^^^^^^

- Fixed parse_search_query to support nested parenthesis and negation operator


0.3.0 (2013-10-01)
^^^^^^^^^^^^^^^^^^

- Added better search query parsing capabilities (support for nested parenthesis, or operator and negation operator)


0.2.1 (2013-08-01)
^^^^^^^^^^^^^^^^^^

- Made psycopg dependency more permissive


0.2.0 (2013-08-01)
^^^^^^^^^^^^^^^^^^

- Added dependency to SQLAlchemy-Utils
- Search vectors must be added manually to each class


0.1.8 (2013-07-30)
^^^^^^^^^^^^^^^^^^

- Fixed safe_search_terms single quote handling


0.1.7 (2013-05-22)
^^^^^^^^^^^^^^^^^^

- Language set explicitly on each query condition


0.1.6 (2013-04-17)
^^^^^^^^^^^^^^^^^^

- Fixed search function when using session based queries


0.1.5 (2013-04-03)
^^^^^^^^^^^^^^^^^^

- Added table name identifier quoting


0.1.4 (2013-01-30)
^^^^^^^^^^^^^^^^^^

- Fixed search_filter func when using empty or undefined search options


0.1.3 (2013-01-30)
^^^^^^^^^^^^^^^^^^

- Added support for custom language parameter in query search functions


0.1.2 (2013-01-30)
^^^^^^^^^^^^^^^^^^

- Added psycopg2 to requirements, fixed travis.yml


0.1.1 (2013-01-12)
^^^^^^^^^^^^^^^^^^

- safe_search_terms support for other than english catalogs


0.1.0 (2013-01-12)
^^^^^^^^^^^^^^^^^^

- Initial public release
