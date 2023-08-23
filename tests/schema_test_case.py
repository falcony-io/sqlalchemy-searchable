import pytest
from sqlalchemy import text


class SchemaTestCase:
    @pytest.fixture
    def should_create_indexes(self):
        return []

    @pytest.fixture
    def should_create_triggers(self):
        return []

    def test_creates_search_index(self, session, should_create_indexes):
        rows = session.execute(
            text(
                """SELECT relname
                FROM pg_class
                WHERE oid IN (
                    SELECT indexrelid
                    FROM pg_index, pg_class
                    WHERE pg_class.relname = 'textitem'
                        AND pg_class.oid = pg_index.indrelid
                        AND indisunique != 't'
                        AND indisprimary != 't'
                ) ORDER BY relname"""
            )
        ).fetchall()
        assert should_create_indexes == [row[0] for row in rows]

    def test_creates_search_trigger(self, session, should_create_triggers):
        rows = session.execute(
            text(
                """SELECT DISTINCT trigger_name
                FROM information_schema.triggers
                WHERE event_object_table = 'textitem'
                AND trigger_schema NOT IN
                    ('pg_catalog', 'information_schema')
                ORDER BY trigger_name"""
            )
        ).fetchall()
        assert should_create_triggers == [row[0] for row in rows]
