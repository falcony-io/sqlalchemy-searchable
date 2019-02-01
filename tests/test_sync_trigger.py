import pytest
import sqlalchemy as sa
from sqlalchemy import text

from sqlalchemy_searchable import sync_trigger, vectorizer


class TestSyncTrigger:
    @pytest.fixture(
        params=[
            "{table}_{column}_trigger",
            "{table}_{column}_trg",
        ]
    )
    def search_trigger_name(self, request):
        return request.param

    @pytest.fixture(
        params=[
            "{table}_{column}_update_trigger",
            "{table}_{column}_update",
        ]
    )
    def search_trigger_function_name(self, request):
        return request.param

    @pytest.fixture(autouse=True)
    def create_tables(self, engine):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE article (
                        name TEXT,
                        content TEXT,
                        "current_user" TEXT,
                        search_vector TSVECTOR
                    );

                    CREATE SCHEMA another;

                    CREATE TABLE another.article (
                        name TEXT,
                        content TEXT,
                        "current_user" TEXT,
                        search_vector TSVECTOR
                    );
                    """
                )
            )

        yield

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    DROP TABLE article;
                    DROP TABLE another.article;
                    DROP SCHEMA another;
                    """
                )
            )

    def test_creates_triggers_and_functions(self, engine, ts_vector_options):
        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                options=ts_vector_options,
            )
            conn.execute(
                text(
                    """INSERT INTO article (name, content)
                    VALUES ('some name', 'some content')"""
                )
            )
            vector = conn.execute(text("SELECT search_vector FROM article")).scalar()
        assert vector == "'content':4 'name':2"

    def test_different_schema(self, engine):
        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                schema="another",
            )
            conn.execute(
                text(
                    """INSERT INTO another.article (name, content)
                     VALUES ('some name', 'some content')"""
                )
            )
            vector = conn.execute(
                text("SELECT search_vector FROM another.article")
            ).scalar()
        assert vector == "'content':4 'name':2"

    def test_updates_column_values(self, engine, ts_vector_options):
        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                options=ts_vector_options,
            )
            conn.execute(
                text(
                    """INSERT INTO article (name, content)
                    VALUES ('some name', 'some content')"""
                )
            )
            conn.execute(text("ALTER TABLE article DROP COLUMN name"))
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["content"],
                options=ts_vector_options,
            )
            vector = conn.execute(text("SELECT search_vector FROM article")).scalar()
        assert vector == "'content':2"

    def test_does_not_update_column_values_when_updating_rows_disabled(
        self, engine, ts_vector_options
    ):
        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                options=ts_vector_options,
            )
            conn.execute(
                text(
                    """INSERT INTO article (name, content)
                    VALUES ('some name', 'some content')"""
                )
            )
            conn.execute(text("ALTER TABLE article DROP COLUMN name"))
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["content"],
                options=ts_vector_options,
                update_rows=False,
            )
            vector = conn.execute(text("SELECT search_vector FROM article")).scalar()
        assert vector == "'content':4 'name':2"

    def test_custom_vectorizers(sel, Base, engine, session, ts_vector_options):
        articles = sa.Table(
            "article",
            Base.metadata,
            autoload_with=session.bind,
        )

        @vectorizer(articles.c.content)
        def vectorize_content(column):
            return sa.func.replace(column, "bad", "good")

        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                metadata=Base.metadata,
                options=ts_vector_options,
            )
            conn.execute(
                text(
                    """INSERT INTO article (name, content)
                    VALUES ('some name', 'some bad content')"""
                )
            )
            vector = conn.execute(text("SELECT search_vector FROM article")).scalar()
        assert vector == "'content':5 'good':4 'name':2"

    def test_trigger_with_reserved_word(self, engine, ts_vector_options):
        with engine.begin() as conn:
            conn.execute(
                text(
                    """INSERT INTO article (name, content, "current_user")
                    VALUES ('some name', 'some bad content', now())"""
                )
            )

            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content", "current_user"],
                options=ts_vector_options,
            )
            # raises ProgrammingError without reserved_words:
            conn.execute(text("UPDATE article SET name=name"))
