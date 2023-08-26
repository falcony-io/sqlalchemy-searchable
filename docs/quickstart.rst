Quick start
===========

.. currentmodule:: sqlalchemy_searchable

Installation
------------

SQLAlchemy-Searchable is available on PyPI_. It can be installed using pip_::

    pip install SQLAlchemy-Searchable

SQLAlchemy-Searchable requires Python 3.8 or newer, either the cPython or PyPy
implementation.

.. _PyPI: https://pypi.python.org/pypi/SQLAlchemy-Searchable
.. _pip: https://pip.pypa.io/

Configuration
-------------

The first step to enable full-text search functionality in your app is to
configure SQLAlchemy-Searchable using :func:`make_searchable` function by
passing it your declarative base class::

    from sqlalchemy.orm import declarative_base
    from sqlalchemy_searchable import make_searchable

    Base = declarative_base()
    make_searchable(Base.metadata)

Define models
-------------

Then, add a search vector column to your model and specify which columns you want to
be included in the full-text search. Here's an example using an ``Article``
model::

    from sqlalchemy import Column, Integer, String, Text
    from sqlalchemy_utils.types import TSVectorType

    class Article(Base):
        __tablename__ = "article"

        id = Column(Integer, primary_key=True)
        name = Column(String(255))
        content = Column(Text)
        search_vector = Column(TSVectorType("name", "content"))

The search vector is a special column of
:class:`~sqlalchemy_utils.types.ts_vector.TSVectorType` data type that is
optimized for text search. Here, we want the ``name`` and ``content`` columns to
be full-text indexed, which we have indicated by giving them as arguments to the
:class:`~sqlalchemy_utils.types.ts_vector.TSVectorType` constructor.

Create and populate the tables
------------------------------

Now, let's create the tables and add some sample data. Before creating the
tables, make sure to call :func:`sqlalchemy.orm.configure_mappers` to ensure
that mappers have been configured for the models::

    from sqlalchemy import create_engine
    from sqlalchemy.orm import configure_mappers, Session

    engine = create_engine("postgresql://localhost/sqlalchemy_searchable_test")
    configure_mappers()  # IMPORTANT!
    Base.metadata.create_all(engine)

    session = Session(engine)

    article1 = Article(name="First article", content="This is the first article")
    article2 = Article(name="Second article", content="This is the second article")

    session.add(article1)
    session.add(article2)
    session.commit()

Performing searches
-------------------

After we've created the articles and populated the database, we can now perform
full-text searches on them using the :func:`~sqlalchemy_searchable.search`
function::

    from sqlalchemy import select
    from sqlalchemy_searchable import search

    query = search(select(Article), "first")
    article = session.scalars(query).first()
    print(article.name)
    # Output: First article

API
---

.. autofunction:: make_searchable
.. autofunction:: search

