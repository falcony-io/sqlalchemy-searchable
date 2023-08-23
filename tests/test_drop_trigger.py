import pytest
from sqlalchemy import text

from sqlalchemy_searchable import drop_trigger, sync_trigger


class TestDropTrigger:
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
                    )
                    """
                )
            )

        yield

        with engine.begin() as conn:
            conn.execute(text("DROP TABLE article"))

    def test_drops_triggers_and_functions(self, engine, ts_vector_options):
        def trigger_exist(conn):
            return conn.execute(
                text(
                    """SELECT COUNT(*)
                    FROM pg_trigger
                    WHERE tgname = :trigger_name
                    """
                ),
                {
                    "trigger_name": ts_vector_options["search_trigger_name"].format(
                        table="article",
                        column="search_vector",
                    )
                },
            ).scalar()

        def function_exist(conn):
            return conn.execute(
                text(
                    """SELECT COUNT(*)
                   FROM pg_proc
                   WHERE proname = :function_name
                   """
                ),
                {
                    "function_name": ts_vector_options[
                        "search_trigger_function_name"
                    ].format(
                        table="article",
                        column="search_vector",
                    )
                },
            ).scalar()

        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                options=ts_vector_options,
            )

            assert trigger_exist(conn) == 1
            assert function_exist(conn) == 1

            drop_trigger(conn, "article", "search_vector", options=ts_vector_options)

            assert trigger_exist(conn) == 0
            assert function_exist(conn) == 0
