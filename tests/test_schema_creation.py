import pytest
import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from tests.schema_test_case import SchemaTestCase


class TestAutomaticallyCreatedSchemaItems(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self):
        return [
            "ix_textitem_content_search_vector",
            "ix_textitem_search_vector",
        ]

    @pytest.fixture
    def should_create_triggers(self):
        return [
            "textitem_content_search_vector_trigger",
            "textitem_search_vector_trigger",
        ]


class TestSearchVectorWithoutColumns(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self):
        return ["ix_textitem_search_vector"]

    @pytest.fixture
    def should_create_triggers(self):
        return []

    @pytest.fixture
    def models(self, Base):
        class TextItem(Base):
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType(auto_index=True))

            content = sa.Column(sa.UnicodeText)
