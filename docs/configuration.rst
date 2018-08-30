Configuration
=============

SQLAlchemy-Searchable provides a number of customization options for the automatically generated
search trigger, index and search_vector columns.

Global configuration options
----------------------------

The following configuration options can be defined globally by passing them to make_searchable function.

* search_trigger_name - name of the search database trigger, default: {table}_search_update

* search_trigger_function_name - the name for the database search vector updating function.

* regconfig - postgresql regconfig to be used, default: pg_catalog.english

Example ::


    make_searchable(options={'regconfig': 'pg_catalog.finnish'})


Changing catalog for search vector
----------------------------------


In the following example we use Finnish regconfig instead of the default English one.
::


    class Article(Base):
        __tablename__ = 'article'

        name = sa.Column(sa.Unicode(255))

        search_vector = TSVectorType('name', regconfig='pg_catalog.finnish')

Weighting search results
------------------------

PostgreSQL supports `weighting search terms`_ with weights A through D.

In this example, we give higher priority to terms appearing in the article title than in the content.
::


    class Article(Base):
        __tablename__ = 'article'

        title = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)

        search_vector = sa.Column(
            TSVectorType('title', 'content',
                         weights={'title': 'A', 'content': 'B'})
        )

Note that in order to see the effect of this weighting, you must search with ``sort=True``

::

    query = session.query(Article)
    query = search(query, 'search text', sort=True)


Multiple search vectors per class
---------------------------------

::

    class Article(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        description = sa.Column(sa.UnicodeText)
        simple_search_vector = sa.Column(TSVectorType('name'))

        fat_search_vector = sa.Column(
            TSVectorType('name', 'content', 'description')
        )


After that, we can choose which search vector to use.
::

    query = session.query(Article)
    query = search(query, 'first', vector=fat_search_vector)


Combined search vectors
-----------------------

Sometimes you may want to search from multiple tables at the same time. This can be achieved using
combined search vectors.

Consider the following model definition. Here each article has one author.

::



    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_utils.types import TSVectorType


    Base = declarative_base()


    class Category(Base):
        __tablename__ = 'category'

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


    import sqlalchemy as sa
    from sqlalchemy_searchable import parse_search_query


    search_query = u'matrix'

    combined_search_vector = Article.search_vector | Category.search_vector

    articles = (
        session.query(Article)
        .join(Category)
        .filter(
            combined_search_vector.match(
                sa.func.tsq_parse(search_query)
            )
        )
    )


This query becomes a little more complex when using left joins. Then you have to take into account situations where Category.search_vector is None using coalesce function.

::


    combined_search_vector = (
        Article.search_vector
        |
        sa.func.coalesce(Category.search_vector, u'')
    )

.. _weighting search terms: http://www.postgresql.org/docs/current/static/textsearch-controls.html#TEXTSEARCH-PARSING-DOCUMENTS
