import sqlalchemy as sa
from pytest import raises
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import vectorizer
from tests import TestCase


class TestTypeVectorizers(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(HSTORE)

            search_vector = sa.Column(
                TSVectorType('name', 'content', regconfig='simple')
            )

            content = sa.Column(sa.UnicodeText)

        @vectorizer(HSTORE)
        def hstore_vectorizer(column):
            return sa.cast(sa.func.avals(column), sa.Text)

        self.Article = Article

    def test_uses_column_vectorizer(self):
        article = self.Article(
            name={'fi': 'Joku artikkeli', 'en': 'Some article'}
        )
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        assert 'article' in article.search_vector
        assert 'joku' in article.search_vector
        assert 'some' in article.search_vector
        assert 'artikkeli' in article.search_vector
        assert 'fi' not in article.search_vector
        assert 'en' not in article.search_vector


class TestColumnVectorizer(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(HSTORE)

            search_vector = sa.Column(
                TSVectorType('name', 'content', regconfig='simple')
            )

            content = sa.Column(sa.String)

        @vectorizer(Article.content)
        def vectorize_content(column):
            return sa.func.replace(column, 'bad', 'good')

        @vectorizer(HSTORE)
        def hstore_vectorizer(column):
            return sa.cast(sa.func.avals(column), sa.Text)

        self.Article = Article

    def test_column_vectorizer_has_priority_over_type_vectorizer(self):
        article = self.Article(
            name={'fi': 'Joku artikkeli', 'en': 'Some article'},
            content='bad'
        )
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        for word in ['article', 'artikkeli', 'good', 'joku', 'some']:
            assert word in article.search_vector

    def test_unknown_vectorizable_type(self):
        with raises(TypeError):
            @vectorizer('some unknown type')
            def my_vectorizer(column):
                pass
