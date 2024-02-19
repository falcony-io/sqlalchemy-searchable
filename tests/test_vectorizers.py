import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import vectorizer


class TestTypeVectorizers:
    @pytest.fixture
    def models(self, Article):
        pass

    @pytest.fixture
    def Article(self, Base):
        class Article(Base):
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(HSTORE)

            search_vector = sa.Column(
                TSVectorType("name", "content", regconfig="simple")
            )

            content = sa.Column(sa.UnicodeText)

        @vectorizer(HSTORE)
        def hstore_vectorizer(column):
            return sa.cast(sa.func.avals(column), sa.Text)

        return Article

    def test_uses_type_vectorizer(self, Article, session):
        article = Article(name={"fi": "Joku artikkeli", "en": "Some article"})
        session.add(article)
        session.commit()
        session.refresh(article)
        assert "article" in article.search_vector
        assert "joku" in article.search_vector
        assert "some" in article.search_vector
        assert "artikkeli" in article.search_vector
        assert "fi" not in article.search_vector
        assert "en" not in article.search_vector


class TestColumnVectorizer:
    @pytest.fixture
    def models(self, Article):
        pass

    @pytest.fixture
    def Article(self, Base):
        class Article(Base):
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(HSTORE)

            search_vector = sa.Column(
                TSVectorType("name", "content", regconfig="simple")
            )

            content = sa.Column(sa.String)

        @vectorizer(Article.content)
        def vectorize_content(column):
            return sa.func.replace(column, "bad", "good")

        @vectorizer(HSTORE)
        def hstore_vectorizer(column):
            return sa.cast(sa.func.avals(column), sa.Text)

        return Article

    def test_column_vectorizer_has_priority_over_type_vectorizer(
        self, Article, session
    ):
        article = Article(
            name={"fi": "Joku artikkeli", "en": "Some article"}, content="bad"
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        for word in ["article", "artikkeli", "good", "joku", "some"]:
            assert word in article.search_vector

    def test_unknown_vectorizable_type(self):
        with pytest.raises(TypeError):

            @vectorizer("some unknown type")
            def my_vectorizer(column):
                pass
