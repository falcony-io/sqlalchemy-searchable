from sqlalchemy_searchable import drop_trigger, sync_trigger
from tests import create_test_cases, TestCase


class DropTriggerTestCase(TestCase):
    def create_models(self):
        pass

    def create_tables(self):
        conn = self.session.bind
        conn.execute(
            '''CREATE TABLE article
            (name TEXT, content TEXT, "current_user" TEXT,
            search_vector TSVECTOR)
            '''
        )

    def drop_tables(self):
        self.session.bind.execute('DROP TABLE article')

    def test_drops_triggers_and_functions(self):
        conn = self.session.bind
        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content']
        )

        def trigger_exist():
            return conn.execute(
                """SELECT COUNT(*)
                   FROM pg_trigger
                   WHERE tgname = 'article_search_vector_trigger'
                """
            ).scalar()

        def function_exist():
            return conn.execute(
                """SELECT COUNT(*)
                   FROM pg_proc
                   WHERE proname = 'article_search_vector_update'
                   """
            ).scalar()

        assert trigger_exist() == 1
        assert function_exist() == 1

        drop_trigger(
            conn,
            'article',
            'search_vector',
        )

        assert trigger_exist() == 0
        assert function_exist() == 0


create_test_cases(DropTriggerTestCase)
