Vectorizers
===========

Vectorizers provide means for turning various column types and columns into fulltext
search vector. While PostgreSQL inherently knows how to vectorize string columns,
situations arise where additional vectorization rules are neede. This section outlines
the process of creating and utilizing vectorization rules for both specific column
instances and column types.

Type vectorizers
----------------

By default, PostgreSQL can only directly vectorize string columns. However, scenarios
may arise where vectorizing non-string columns becomes essential. For instance, when
dealing with an :class:`~sqlalchemy.dialects.postgresql.HSTORE` column within your model
that requires fulltext indexing, a dedicated vectorization rule must be defined.

To establish a vectorization rule, use the :data:`~sqlalchemy_searchable.vectorizer`
decorator. The subsequent example demonstrates how to apply a vectorization rule to the
values within all :class:`~sqlalchemy.dialects.postgresql.HSTORE`-typed columns present
in your models::

    from sqlalchemy import cast, func, Text
    from sqlalchemy.dialects.postgresql import HSTORE
    from sqlalchemy_searchable import vectorizer


    @vectorizer(HSTORE)
    def hstore_vectorizer(column):
        return cast(func.avals(column), Text)

The expression returned by the vectorizer is then employed for all fulltext indexed
columns of type :class:`~sqlalchemy.dialects.postgresql.HSTORE`. Consider the following
model as an illustration::

    from sqlalchemy import Column, Integer
    from sqlalchemy_utils import TSVectorType


    class Article(Base):
        __tablename__ = 'article'

        id = Column(Integer, primary_key=True, autoincrement=True)
        name_translations = Column(HSTORE)
        content_translations = Column(HSTORE)
        search_vector = Column(
            TSVectorType(
                "name_translations",
                "content_translations",
            )
        )

In this scenario, SQLAlchemy-Searchable would create the following search trigger for
the model using the default configuration:

.. code-block:: postgres

        CREATE FUNCTION
            article_search_vector_update() RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = to_tsvector(
                'pg_catalog.english',
                coalesce(CAST(avals(NEW.name_translations) AS TEXT), '')
            ) || to_tsvector(
                'pg_catalog.english',
                coalesce(CAST(avals(NEW.content_translations) AS TEXT), '')
            );
            RETURN NEW;
        END
        $$ LANGUAGE 'plpgsql';


Column vectorizers
------------------

Sometimes you may want to set special vectorizer only for specific column. This
can be achieved as follows::

    class Article(Base):
        __tablename__ = "article"

        id = Column(Integer, primary_key=True, autoincrement=True)
        name_translations = Column(HSTORE)
        search_vector = Column(TSVectorType("name_translations"))


    @vectorizer(Article.name_translations)
    def name_vectorizer(column):
        return cast(func.avals(column), Text)


.. note::

    Column vectorizers always have precedence over type vectorizers.

API
^^^

.. currentmodule:: sqlalchemy_searchable
.. autodata:: vectorizer
.. autoclass:: Vectorizer
   :members:
   :special-members: __call__
