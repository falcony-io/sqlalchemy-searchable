SQLAlchemy-Searchable
=====================


SQLAlchemy-Searchable provides FullText search capabilities for SQLAlchemy models. Currently only supports PostgreSQL.


QuickStart
==========

1. Make your SQLAlchemy declarative model inherit Searchable mixin.
2. Define searchable columns and custom search configuration


First let's define a simple Article model. This model has three fields: id, name and content.
We want the name and content to be fulltext indexed, hence we put them in special __searchable_columns__ property.
::

    import sqlalchemy as sa
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_searchable import Searchable, SearchQueryMixin


    Base = declarative_base()


    class Article(Base, Searchable):
        __tablename__ = 'article'
        __searchable_columns = ['name', 'content']

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)


Now lets create some dummy data. ::

    engine = create_engine('postgres://localhost/sqlalchemy_searchable_test')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    article1 = Article(name=u'First article', content=u'This is the first article')
    article2 = Article(name=u'Second article', content=u'This is the second article')

    session.add(article1)
    session.add(article2)
    session.commit()


After we've created the articles, we can search trhough them. ::

    from sqlalchemy_searchable import search


    query = session.query(Article)

    query = search(query, 'first')

    print query.first().name
    >>> First article



