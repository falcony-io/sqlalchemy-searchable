import pytest
import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import search
from tests.schema_test_case import SchemaTestCase


class TestMultipleSearchVectorsPerClass(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self):
        return [
            "ix_textitem_content_vector",
            "ix_textitem_name_vector",
        ]

    @pytest.fixture
    def should_create_triggers(self):
        return [
            "textitem_content_vector_trigger",
            "textitem_name_vector_trigger",
        ]

    @pytest.fixture
    def models(self, Base):
        class TextItem(Base):
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            content = sa.Column(sa.UnicodeText)

            name_vector = sa.Column(TSVectorType("name", auto_index=True))

            content_vector = sa.Column(TSVectorType("content", auto_index=True))


class TestMultipleSearchVectorsSearchFunction:
    @pytest.fixture
    def TextMultiItem(self, Base):
        class TextMultiItem(Base):
            __tablename__ = "textmultiitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            name_vector = sa.Column(TSVectorType("name", auto_index=False))
            content_vector = sa.Column(TSVectorType("content", auto_index=False))

        return TextMultiItem

    @pytest.fixture
    def models(self, TextMultiItem):
        pass

    def test_choose_vector(self, session, TextMultiItem):
        session.add(TextMultiItem(name="index", content="lorem ipsum"))
        session.add(TextMultiItem(name="ipsum", content="admin content"))
        session.commit()

        s1 = search(sa.select(TextMultiItem), "ipsum", vector=TextMultiItem.name_vector)
        assert session.scalars(s1).first().name == "ipsum"

    def test_without_auto_index(self, TextMultiItem):
        indexes = TextMultiItem.__table__.indexes
        assert indexes == set()
