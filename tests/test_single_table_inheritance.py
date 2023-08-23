import pytest
import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from tests.schema_test_case import SchemaTestCase


class TestSearchableWithSingleTableInheritance(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self):
        return ["ix_textitem_search_vector"]

    @pytest.fixture
    def should_create_triggers(self):
        return ["textitem_search_vector_trigger"]

    @pytest.fixture
    def models(self, Base):
        class TextItem(Base):
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType("name", "content"))

            content = sa.Column(sa.UnicodeText)

        class Article(TextItem):
            created_at = sa.Column(sa.DateTime)
