from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import vectorizer


class TestTypeVectorizers:
    @pytest.fixture
    def models(self, Article: type[Any]) -> None:
        pass

    @pytest.fixture
    def Article(self, Base: type[DeclarativeBase]) -> type[Any]:
        class Article(Base):  # type: ignore[valid-type, misc]
            __tablename__ = "textitem"

            id: Mapped[int] = mapped_column(primary_key=True)

            name: Mapped[dict[str, str]] = mapped_column(HSTORE)

            search_vector: Mapped[TSVectorType] = mapped_column(
                TSVectorType("name", "content", regconfig="simple")
            )

            content: Mapped[str | None]

        @vectorizer(HSTORE)
        def hstore_vectorizer(column: sa.ColumnClause[Any]) -> sa.ColumnElement[str]:
            return sa.cast(sa.func.avals(column), sa.Text)

        return Article

    def test_uses_type_vectorizer(self, Article: type[Any], session: Session) -> None:
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
    def models(self, Article: type[Any]) -> None:
        pass

    @pytest.fixture
    def Article(self, Base: type[DeclarativeBase]) -> type[Any]:
        class Article(Base):  # type: ignore[valid-type, misc]
            __tablename__ = "textitem"

            id: Mapped[int] = mapped_column(primary_key=True)

            name: Mapped[dict[str, str]] = mapped_column(HSTORE)

            search_vector: Mapped[TSVectorType] = mapped_column(
                TSVectorType("name", "content", regconfig="simple")
            )

            content: Mapped[str]

        @vectorizer(Article.content)
        def vectorize_content(column: sa.ColumnClause[Any]) -> sa.ColumnElement[str]:
            return sa.func.replace(column, "bad", "good")

        @vectorizer(HSTORE)
        def hstore_vectorizer(column: sa.ColumnClause[Any]) -> sa.ColumnElement[str]:
            return sa.cast(sa.func.avals(column), sa.Text)

        return Article

    def test_column_vectorizer_has_priority_over_type_vectorizer(
        self,
        Article: type[Any],
        session: Session,
    ) -> None:
        article = Article(
            name={"fi": "Joku artikkeli", "en": "Some article"}, content="bad"
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        for word in ["article", "artikkeli", "good", "joku", "some"]:
            assert word in article.search_vector

    def test_unknown_vectorizable_type(self) -> None:
        with pytest.raises(TypeError):

            @vectorizer("some unknown type")  # type: ignore[arg-type]
            def my_vectorizer(column: Any) -> Any:
                pass
