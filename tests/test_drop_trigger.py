from sqlalchemy_searchable import drop_trigger, sync_trigger
from tests import create_test_cases, TestCase


class DropTriggerTestCase(TestCase):
    def create_models(self):
        pass

    def create_tables(self):
        with self.engine.begin() as conn:
            conn.execute(
                """
                CREATE TABLE article (
                    name TEXT,
                    content TEXT,
                    "current_user" TEXT,
                    search_vector TSVECTOR
                )
                """
            )

    def drop_tables(self):
        with self.engine.begin() as conn:
            conn.execute("DROP TABLE article")

    def test_drops_triggers_and_functions(self):
        def trigger_exist(conn):
            return conn.execute(
                """SELECT COUNT(*)
                   FROM pg_trigger
                   WHERE tgname = 'article_search_vector_trigger'
                """
            ).scalar()

        def function_exist(conn):
            return conn.execute(
                """SELECT COUNT(*)
                   FROM pg_proc
                   WHERE proname = 'article_search_vector_update'
                   """
            ).scalar()

        with self.engine.begin() as conn:
            sync_trigger(conn, "article", "search_vector", ["name", "content"])

            assert trigger_exist(conn) == 1
            assert function_exist(conn) == 1

            drop_trigger(conn, "article", "search_vector")

            assert trigger_exist(conn) == 0
            assert function_exist(conn) == 0


create_test_cases(DropTriggerTestCase)
