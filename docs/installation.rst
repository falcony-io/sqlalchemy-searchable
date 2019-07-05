Installation
------------

::

    pip install SQLAlchemy-Searchable


Supported versions are python 2.7 and 3.3+.


QuickStart
----------

1. Import and call make_searchable function.

2. Define TSVectorType columns in your SQLAlchemy declarative model.


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


Now lets create the tables and some dummy data. It is very important here that you either
access your searchable class or call ``configure_mappers`` before the creation of tables. SA-Searchable adds DDL listeners on the configuration phase of models.
::


    engine = create_engine('postgresql://localhost/sqlalchemy_searchable_test')
    sa.orm.configure_mappers()  # IMPORTANT!
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    article1 = Article(name=u'First article', content=u'This is the first article')
    article2 = Article(name=u'Second article', content=u'This is the second article')

    session.add(article1)
    session.add(article2)
    session.commit()


After we've created the articles, we can search through them.
::


    from sqlalchemy_searchable import search


    query = session.query(Article)

    query = search(query, 'first')

    print query.first().name
    # First article

Optionally specify ``sort=True`` to get results in order of relevance (ts_rank_cd_)::

    query = search(query, 'first', sort=True)

.. _ts_rank_cd: http://www.postgresql.org/docs/devel/static/textsearch-controls.html#TEXTSEARCH-RANKING
