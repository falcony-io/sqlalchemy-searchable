SQLAlchemy-Searchable
=====================


SQLAlchemy-Searchable provides `full text search`_ capabilities for SQLAlchemy_ models. Currently it only supports PostgreSQL_.


Installation
------------

::

    pip install SQLAlchemy-Searchable


Supported versions are python 2.6, 2.7 and 3.3.


QuickStart
----------

1. Import and call make_searchable function.

2. Define TSVectorType columns to your SQLAlchemy declarative model.


First let's define a simple Article model. This model has three fields: id, name and content.
We want the name and content to be fulltext indexed, hence we put them inside the definition of TSVectorType.
::

    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy_searchable import make_searchable
    from sqlalchemy_utils.types import TSVectorType


    Base = declarative_base()

    make_searchable()


    class Article(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType('name', 'content'))


Now lets create some dummy data.
::


    engine = create_engine('postgres://localhost/sqlalchemy_searchable_test')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    article1 = Article(name=u'First article', content=u'This is the first article')
    article2 = Article(name=u'Second article', content=u'This is the second article')

    session.add(article1)
    session.add(article2)
    session.commit()


After we've created the articles, we can search trhough them.
::


    from sqlalchemy_searchable import search


    query = session.query(Article)

    query = search(query, 'first')

    print query.first().name
    >>> First article


Multiple search vectors per class
=================================

::

    class Article(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        description = sa.Column(sa.UnicodeText)
        simple_search_vector = sa.Column(TSVectorType('name'))

        fat_search_vector = sa.Column(
            TSVectorType('name', 'content', 'desription')
        )

After that, we can choose which search vector to use.
::

    query = session.query(Article)
    query = search(query, 'first', vector=fat_search_vector)


Search query operators
======================

As of version 0.3.0 SQLAlchemy-Searchable comes with built in search query parser. The search query parser is capable of parsing human readable search queries into PostgreSQL search query syntax.


Basic operators
---------------

AND operator
^^^^^^^^^^^^

Example: Search for articles containing 'star' and 'wars'

The default operator is 'and', hence the following queries are essentially the same:

::

    query = search(query, 'star wars')
    query2 = search(query, 'star and wars')
    assert query == query2

OR operator
^^^^^^^^^^^

Searching for articles containing 'star' or 'wars'

::


    query = search(query, 'star or wars')


Negation operator
^^^^^^^^^^^^^^^^^

SQLAlchemy-Searchable search query parser supports negation operator. By default the negation operator is '-'.

Example: Searching for article containing 'star' but not 'wars'

::


    query = search(query, 'star or -wars')



Using parenthesis
-----------------

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


Search options
==============

SQLAlchemy-Searchable provides number of customization options for the automatically generated
search trigger, index and search_vector columns.

Global configuration options
----------------------------

The following configuration options can be defined globally by passing them to make_searchable function.

* search_vector_name - name of the search vector column, default: search_vector

* search_trigger_name - name of the search database trigger, default: {table}_search_update

* search_index_name - name of the search index, default: {table}_search_index

* search_trigger_function_name - the name for the database search vector updating function. This configuration option is only used if remove_hyphens is set as `True` otherwise the builtin postgresql `tsvector_update_trigger` is used for updating search vectors.

* catalog - postgresql catalog to be used, default: pg_catalog.english

* remove_hyphens - boolean indicating whether or not hyphen marks should be removed from values that are search vectorized. If this is set as `True` a separate database function is created that strips the hyphens whenever search vector gets updated. Since '-' is used as a negation operator it is strongly encouraged that this is set as `True`. This defaults to `True` as of version 0.5.0.


Example ::


    make_searchable(options={'catalog': 'pg_catalog.finnish'})


Changing catalog for search vector
----------------------------------


In the following example we use Finnish catalog instead of the default English one.
::


    class Article(Base):
        __tablename__ = 'article'

        name = sa.Column(sa.Unicode(255))

        search_vector = TSVectorType('name', catalog='pg_catalog.finnish')


Combined search vectors
=======================

Sometimes you may want to search from multiple tables at the same time. This can be achieved using
combined search vectors.

Consider the following model definition. Here each article has one author.

::



    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_utils.types import TSVectorType


    Base = declarative_base()


    class Category(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        search_vector = sa.Column(TSVectorType('name'))


    class Article(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType('name', 'content'))
        category_id = sa.Column(
            sa.Integer,
            sa.ForeignKey(Category.id)
        )
        category = sa.orm.relationship(Category)


Now consider a situation where we want to find all articles, where either article content or name or category name contains the word 'matrix'. This can be achieved as follows:

::


    from sqlalchemy_searchable import parse_search_query
    from sqlalchemy_utils.expressions import (
        tsvector_match, tsvector_concat, to_tsquery
    )

    search_query = u'matrix'

    combined_search_vector = tsvector_concat(
        Article.search_vector,
        Category.search_vector
    )

    articles = (
        session.query(Article)
        .join(Category)
        .filter(
            tsvector_match(
                combined_search_vector,
                to_tsquery(
                    'simple',
                    parse_search_query(search_query)
                ),
            )
        )
    )


This query becomes a little more complex when using left joins. Then you have to take into account situations where Category.search_vector is None using coalesce function.

::


    combined_search_vector = tsvector_concat(
        Article.search_vector,
        sa.func.coalesce(Category.search_vector, u'')
    )



Flask-SQLAlchemy integration
============================

SQLAlchemy-Searchable can be neatly integrated into Flask-SQLAlchemy using SearchQueryMixin class.


Example ::

    from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
    from sqlalchemy_searchable import SearchQueryMixin
    from sqlalchemy_utils.types import TSVectorType


    db = SQLAlchemy()


    class ArticleQuery(BaseQuery, SearchQueryMixin):
        pass


    class Article(db.Model):
        query_class = ArticleQuery
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType('name', 'content'))


Now this is where the fun begins! SearchQueryMixin provides search method for ArticleQuery. You can chain calls just like when using query filter calls.
Here we search for first 5 articles that contain the word 'Finland'.
::

    Article.query.search(u'Finland').limit(5).all()



.. _`full text search`: http://en.wikipedia.org/wiki/Full_text_search
.. _SQLAlchemy: http://http://www.sqlalchemy.org/
.. _PostgreSQL: http://www.postgresql.org/


