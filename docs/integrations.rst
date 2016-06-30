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
    
    db.configure_mappers() #very important!
    db.create_all()
    db.commit()


Now this is where the fun begins! SearchQueryMixin provides a search method for ArticleQuery. You can chain calls just like when using query filter calls.
Here we search for first 5 articles that contain the word 'Finland'.
::

    Article.query.search(u'Finland').limit(5).all()

When using Flask-SQLAlchemy, the columns of your models might be set to various DataTypes(i.e db.Datetime, db.String, db.Integer, etc.). As of 30/06/2016, SQLAlchemy-searchable does not support those datatypes and returns a TypeError when said columns are implemented in the search vector. Instead, use Unicode and UnicodeText accordingly. 
