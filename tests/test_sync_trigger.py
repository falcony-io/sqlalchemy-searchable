from sqlalchemy_searchable import sync_trigger

from tests import TestCase, create_test_cases


class SyncTriggerTestCase(TestCase):
    def create_models(self):
        pass

    def create_tables(self):
        conn = self.session.bind
        conn.execute(
            '''CREATE TABLE article
            (name TEXT, content TEXT, search_vector TSVECTOR)
            '''
        )

    def drop_tables(self):
        self.session.bind.execute('DROP TABLE article')

    def test_creates_triggers_and_functions(self):
        conn = self.session.bind
        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content']
        )
        conn.execute(
            '''INSERT INTO article (name, content)
            VALUES ('some name', 'some content')'''
        )
        vector = conn.execute('SELECT search_vector FROM article').scalar()
        assert vector == "'content':4 'name':2"

    def test_updates_column_values(self):
        conn = self.session.bind
        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content']
        )
        conn.execute(
            '''INSERT INTO article (name, content)
            VALUES ('some name', 'some content')'''
        )
        conn.execute('ALTER TABLE article DROP COLUMN name')
        sync_trigger(conn, 'article', 'search_vector', ['content'])
        vector = conn.execute('SELECT search_vector FROM article').scalar()
        assert vector == "'content':2"


create_test_cases(SyncTriggerTestCase)
