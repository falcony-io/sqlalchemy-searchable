from tests import TestCase


class TestAutomaticallyCreatedSchemaItems(TestCase):
    def test_creates_search_index(self):
        rows = self.session.execute(
            """SELECT relname
            FROM pg_class
            WHERE oid IN (
                SELECT indexrelid
                FROM pg_index, pg_class
                WHERE pg_class.relname='textitem'
                    AND pg_class.oid=pg_index.indrelid
                    AND indisunique != 't'
                    AND indisprimary != 't'
            )"""
        ).fetchall()
        assert 'textitem_search_index' in map(lambda a: a[0], rows)

    def test_creates_search_trigger(self):
        rows = self.session.execute(
            """SELECT DISTINCT trigger_name
            FROM information_schema.triggers
            WHERE event_object_table = 'textitem'
            AND trigger_schema NOT IN
            ('pg_catalog', 'information_schema')"""
        ).fetchall()
        assert 'textitem_search_update' in map(lambda a: a[0], rows)

    def test_creates_search_vector_column(self):
        rows = self.session.execute(
            """SELECT column_name
            FROM information_schema.columns WHERE table_name = 'textitem'"""
        ).fetchall()
        assert 'search_vector' in map(lambda a: a[0], rows)
