from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from sqlalchemy_searchable import drop_trigger, SearchOptions, sync_trigger


class TestDropTrigger:
    @pytest.fixture(
        params=[
            "{table}_{column}_trigger",
            "{table}_{column}_trg",
        ]
    )
    def search_trigger_name(self, request: pytest.FixtureRequest) -> Any:
        return request.param

    @pytest.fixture(
        params=[
            "{table}_{column}_update_trigger",
            "{table}_{column}_update",
        ]
    )
    def search_trigger_function_name(self, request: pytest.FixtureRequest) -> Any:
        return request.param

    @pytest.fixture(autouse=True)
    def create_tables(self, engine: Engine) -> Generator[None, None, None]:
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

    def test_drops_triggers_and_functions(
        self,
        engine: Engine,
        search_options: SearchOptions,
    ) -> None:
        def trigger_exist(conn: Connection) -> Any:
            return conn.execute(
                text(
                    """SELECT COUNT(*)
                    FROM pg_trigger
                    WHERE tgname = :trigger_name
                    """
                ),
                {
                    "trigger_name": search_options.search_trigger_name.format(
                        table="article",
                        column="search_vector",
                    )
                },
            ).scalar_one()

        def function_exist(conn: Connection) -> Any:
            return conn.execute(
                text(
                    """SELECT COUNT(*)
                   FROM pg_proc
                   WHERE proname = :function_name
                   """
                ),
                {
                    "function_name": search_options.search_trigger_function_name.format(
                        table="article",
                        column="search_vector",
                    )
                },
            ).scalar_one()

        with engine.begin() as conn:
            sync_trigger(
                conn,
                "article",
                "search_vector",
                ["name", "content"],
                options=search_options,
            )

            assert trigger_exist(conn) == 1
            assert function_exist(conn) == 1

            drop_trigger(conn, "article", "search_vector", options=search_options)

            assert trigger_exist(conn) == 0
            assert function_exist(conn) == 0
