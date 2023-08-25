Flask-SQLAlchemy integration
----------------------------

.. warning::
    The query interface is considered legacy in SQLAlchemy. Prefer using
    ``session.execute(search(...))`` instead.

SQLAlchemy-Searchable can be integrated into Flask-SQLAlchemy using
``SearchQueryMixin`` class::

    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_sqlalchemy.query import Query
    from sqlalchemy_utils.types import TSVectorType
    from sqlalchemy_searchable import SearchQueryMixin, make_searchable

    app = Flask(__name__)
    db = SQLAlchemy(app)

    make_searchable(db.metadata)


    class ArticleQuery(Query, SearchQueryMixin):
        pass


    class Article(db.Model):
        query_class = ArticleQuery
        __tablename__ = "article"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255))
        content = db.Column(db.Text)
        search_vector = db.Column(TSVectorType("name", "content"))


    db.configure_mappers()  # very important!

    with app.app_context():
        db.create_all()

The ``SearchQueryMixin`` provides a ``search`` method to ``ArticleQuery``. You
can chain calls just like when using query filter calls. Here we search for
first five articles that contain the word "Finland"::

    Article.query.search("Finland").limit(5).all()
