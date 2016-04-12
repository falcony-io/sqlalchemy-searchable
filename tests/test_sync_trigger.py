import sqlalchemy as sa

from sqlalchemy_searchable import sync_trigger, vectorizer
from tests import create_test_cases, TestCase


class SyncTriggerTestCase(TestCase):
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

    def test_custom_vectorizers(self):
        articles = sa.Table(
            'article',
            self.Base.metadata,
            autoload=True,
            autoload_with=self.session.bind
        )

        @vectorizer(articles.c.content)
        def vectorize_content(column):
            return sa.func.replace(column, 'bad', 'good')

        conn = self.session.bind
        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content'],
            metadata=self.Base.metadata
        )
        conn.execute(
            '''INSERT INTO article (name, content)
            VALUES ('some name', 'some bad content')'''
        )
        vector = conn.execute('SELECT search_vector FROM article').scalar()
        assert vector == "'content':5 'good':4 'name':2"

    def test_trigger_with_reserved_word(self):
        conn = self.session.bind
        conn.execute(
            '''INSERT INTO article (name, content, "current_user")
            VALUES ('some name', 'some bad content', now())'''
        )

        sync_trigger(
            conn,
            'article',
            'search_vector',
            ['name', 'content', 'current_user']
        )
        # raises ProgrammingError without reserved_words:
        conn.execute(
            '''UPDATE article SET name=name'''
        )


create_test_cases(SyncTriggerTestCase)
