Configuration
=============

.. currentmodule:: sqlalchemy_searchable

SQLAlchemy-Searchable provides a number of customization options for the automatically generated
search trigger, index and search vector columns.

Global configuration options
----------------------------

The following configuration options can be defined globally by passing them to
:func:`make_searchable` function:

``search_trigger_name``
    Defines the name of the search database trigger. The default naming
    convention is ``"{table}_{column}_trigger"``.

``search_trigger_function_name``
    Defines the name of the database search vector updating function. The
    default naming convention is ``{table}_{column}_update``.

``regconfig``
    This is the PostgreSQL text search configuration that determines the
    language configuration used for searching. The default setting is
    ``"pg_catalog.english"``.

Here's an example of how to leverage these options::

    make_searchable(Base.metadata, options={"regconfig": "pg_catalog.finnish"})

Changing catalog for search vector
----------------------------------

In some cases, you might want to switch from the default language configuration
to another language for your search vector. You can achieve this by providing
the ``regconfig`` parameter for the
:class:`~sqlalchemy_utils.types.ts_vector.TSVectorType`. In the following
example, we use Finnish instead of the default English one::

    class Article(Base):
        __tablename__ = "article"

        name = sa.Column(sa.Text(255))
        search_vector = TSVectorType("name", regconfig="pg_catalog.finnish")

Weighting search results
------------------------

To further refine your search results, PostgreSQL's `term weighting system`_
(ranging from A to D) can be applied. This example demonstrates how to
prioritize terms found in the article title over those in the content::

    class Article(Base):
        __tablename__ = "article"

        id = sa.Column(sa.Integer, primary_key=True)
        title = sa.Column(sa.String(255))
        content = sa.Column(sa.Text)
        search_vector = sa.Column(
            TSVectorType("title", "content", weights={"title": "A", "content": "B"})
        )

Remember, when working with weighted search terms, you need to conduct your
searches using the ``sort=True`` option::

    query = search(sa.select(Article), "search text", sort=True)

.. _term weighting system: http://www.postgresql.org/docs/current/static/textsearch-controls.html#TEXTSEARCH-PARSING-DOCUMENTS

Multiple search vectors per class
---------------------------------

In cases where a model requires multiple search vectors, SQLAlchemy-Searchable
has you covered. Here's how you can set up multiple search vectors for an
``Article`` class::

    class Article(Base):
        __tablename__ = "article"

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(255))
        content = sa.Column(sa.Text)
        description = sa.Column(sa.Text)
        simple_search_vector = sa.Column(TSVectorType("name"))

        fat_search_vector = sa.Column(TSVectorType("name", "content", "description"))

You can then choose which search vector to use when querying::

    query = search(sa.select(Article), "first", vector=Article.fat_search_vector)

Combined search vectors
-----------------------

Sometimes you may want to search from multiple tables at the same time. This can
be achieved using combined search vectors. Consider the following model
definition where each article has one category::

    import sqlalchemy as sa
    from sqlalchemy.orm import declarative_base
    from sqlalchemy_utils.types import TSVectorType

    Base = declarative_base()


    class Category(Base):
        __tablename__ = "category"

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(255))
        search_vector = sa.Column(TSVectorType("name"))


    class Article(Base):
        __tablename__ = "article"

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(255))
        content = sa.Column(sa.Text)
        search_vector = sa.Column(TSVectorType("name", "content"))
        category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))
        category = sa.orm.relationship(Category)

Now consider a situation where we want to find all articles where either article
content or name or category name contains the word "matrix". This can be
achieved as follows::

    combined_search_vector = Article.search_vector | Category.search_vector
    query = search(
        sa.select(Article).join(Category), "matrix", vector=combined_search_vector
    )

This query becomes a little more complex when using left joins. Then, you have
to take into account situations where ``Category.search_vector`` might be
``None`` using the ``coalesce`` function::

    combined_search_vector = Article.search_vector | sa.func.coalesce(
        Category.search_vector, ""
    )
