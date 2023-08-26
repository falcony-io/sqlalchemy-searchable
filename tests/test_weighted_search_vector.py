import re

import pytest
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import search
from tests.schema_test_case import SchemaTestCase


@pytest.fixture
def models(WeightedTextItem):
    pass


@pytest.fixture
def WeightedTextItem(Base):
    class WeightedTextItem(Base):
        __tablename__ = "textitem"

        id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
        search_vector = sa.Column(
            TSVectorType("name", "content", weights={"name": "A", "content": "B"})
        )

    return WeightedTextItem


class TestCreateWeightedSearchVector(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self):
        return ["ix_textitem_search_vector"]

    @pytest.fixture
    def should_create_triggers(self):
        return ["textitem_search_vector_trigger"]

    def test_search_function_weights(self, session):
        func_name = "textitem_search_vector_update"
        sql = text("SELECT proname,prosrc FROM pg_proc WHERE proname=:name")
        name, src = session.execute(sql, {"name": func_name}).fetchone()
        pattern = (
            r"setweight\(to_tsvector\(.+?"
            r"coalesce\(NEW.(\w+).+?"
            r"\)\), '([A-D])'\)"
        )
        first, second = (match.groups() for match in re.finditer(pattern, src))
        assert first == ("name", "A")
        assert second == ("content", "B")


class TestWeightedSearchFunction:
    @pytest.fixture(autouse=True)
    def items(self, session, WeightedTextItem):
        session.add(WeightedTextItem(name="Gort", content="Klaatu barada nikto"))
        session.add(WeightedTextItem(name="Klaatu", content="barada nikto"))
        session.commit()

    def test_weighted_search_results(self, session, WeightedTextItem):
        first, second = session.scalars(
            search(sa.select(WeightedTextItem), "klaatu", sort=True)
        ).all()
        assert first.search_vector == "'barada':2B 'klaatu':1A 'nikto':3B"
        assert second.search_vector == "'barada':3B 'gort':1A 'klaatu':2B 'nikto':4B"
