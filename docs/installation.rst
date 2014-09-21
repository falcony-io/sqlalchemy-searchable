Installation
------------

::

    pip install SQLAlchemy-Searchable


Supported versions are python 2.6, 2.7, 3.3 and 3.4.


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
    # First article
