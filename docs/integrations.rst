Flask-SQLAlchemy integration
----------------------------

SQLAlchemy-Searchable can be neatly integrated into Flask-SQLAlchemy using SearchQueryMixin class.


Example ::

    from flask.ext.sqlalchemy import SQLAlchemy, BaseQuery
    from sqlalchemy_searchable import SearchQueryMixin
    from sqlalchemy_utils.types import TSVectorType
    from sqlalchemy_searchable import make_searchable

    db = SQLAlchemy()
    
    make_searchable()


    class ArticleQuery(BaseQuery, SearchQueryMixin):
        pass


    class Article(db.Model):
        query_class = ArticleQuery
        __tablename__ = 'article'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.Unicode(255))
        content = db.Column(db.UnicodeText)
        search_vector = db.Column(TSVectorType('name', 'content'))


Now this is where the fun begins! SearchQueryMixin provides search method for ArticleQuery. You can chain calls just like when using query filter calls.
Here we search for first 5 articles that contain the word 'Finland'.
::

    Article.query.search(u'Finland').limit(5).all()
