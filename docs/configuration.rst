Configuration
=============

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

* remove_symbols - String indicating all symbols that should be removed and converted to emptry strings in each search vectorized column. By default this is `-@.`, meaning all `-`, `@` and `.` will be converted to empty strings.

Before version 0.7.0 this configuration option was known as 'remove_hyphens' and provided only limited conversion of `-` symbols to empty strings.


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
            TSVectorType('name', 'content', 'desription')
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
