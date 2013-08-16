SQLAlchemy-Searchable
=====================


SQLAlchemy-Searchable provides FullText search capabilities for SQLAlchemy models. Currently it only supports PostgreSQL.


QuickStart
----------

1. Make your SQLAlchemy declarative model inherit Searchable mixin.
2. Define searchable columns and custom search configuration
3. Define search_vector


First let's define a simple Article model. This model has three fields: id, name and content.
We want the name and content to be fulltext indexed, hence we put them in special __searchable_columns__ property.
::

    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_searchable import Searchable
    from sqlalchemy_utils.types import TSVectorType


    Base = declarative_base()


    class Article(Base, Searchable):
        __tablename__ = 'article'
        __searchable_columns__ = ['name', 'content']

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType)


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


Search options
--------------

SQLAlchemy-Searchable provides number of customization options for the automatically generated
search trigger, index and search_vector columns.

You can define the custom search options in your model by defining __search_options__ property.
In the following example we use Finnish catalog instead of the default English one.
::


    class Article(Base, Searchable):
        __tablename__ = 'article'
        __searchable_columns__ = ['name', 'content']

        __search_options__ = {
            'catalog': 'pg_catalog.finnish'
        }


* search_vector_name - name of the search vector column, default: search_vector

* search_trigger_name - name of the search database trigger, default: {table}_search_update

* search_index_name - name of the search index, default: {table}_search_index

* catalog - postgresql catalog to be used, default: pg_catalog.english


Combined search vectors
-----------------------

Sometimes you may want to search from multiple tables at the same time. This can be achieved using
combined search vectors.

Consider the following model definition. Here each article has one author.

::



    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_searchable import Searchable
    from sqlalchemy_utils.types import TSVectorType


    Base = declarative_base()


    class Category(Base, Searchable):
        __tablename__ = 'article'
        __searchable_columns__ = ['name']

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        search_vector = sa.Column(TSVectorType)


    class Article(Base, Searchable):
        __tablename__ = 'article'
        __searchable_columns__ = ['name', 'content']

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType)
        category_id = sa.Column(
            sa.Integer,
            sa.ForeignKey(Category.id)
        )
        category = sa.orm.relationship(Category)


Now consider a situation where we want to find all articles, where either article content or name or category name contains the word 'matrix'. This can be achieved as follows:

::


    from sqlalchemy_searchable import safe_search_terms
    from sqlalchemy_utils import tsvector_match, tsvector_concat, to_tsquery


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
                    u' & '.join(safe_search_terms(search_query))
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
----------------------------

SQLAlchemy-Searchable can be neatly integrated into Flask-SQLAlchemy using SearchQueryMixin class.


Example ::

    from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
    from sqlalchemy_searchable import SearchQueryMixin
    from sqlalchemy_utils.types import TSVectorType


    db = SQLAlchemy()


    class ArticleQuery(BaseQuery, SearchQueryMixin):
        pass


    class Article(db.Model, Searchable):
        query_class = ArticleQuery
        __tablename__ = 'article'
        __searchable_columns__ = ['name', 'content']

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(TSVectorType)


Now this is where the fun begins! SearchQueryMixin provides search method for ArticleQuery. You can chain calls just like when using query filter calls.
Here we search for first 5 articles that contain the word 'Finland'.
::

    Article.query.search(u'Finland').limit(5).all()







