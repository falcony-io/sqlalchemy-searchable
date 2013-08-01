Changelog
---------

Here you can see the full list of changes between each SQLAlchemy-Searchable release.


0.2.1 (2013-08-01)
^^^^^^^^^^^^^^^^^^

- Made psycopg dependency more permissive


0.2.0 (2013-08-01)
^^^^^^^^^^^^^^^^^^

- Added dependency to SQLAlchemy-Utils
- Search vectors must be added manually to each class


0.1.7 (2013-07-30)
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
