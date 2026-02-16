import pytest
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_utils import TSVectorType

from tests.schema_test_case import SchemaTestCase


class TestAutomaticallyCreatedSchemaItems(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self) -> list[str]:
        return [
            "ix_textitem_content_search_vector",
            "ix_textitem_search_vector",
        ]

    @pytest.fixture
    def should_create_triggers(self) -> list[str]:
        return [
            "textitem_content_search_vector_trigger",
            "textitem_search_vector_trigger",
        ]


class TestSearchVectorWithoutColumns(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self) -> list[str]:
        return ["ix_textitem_search_vector"]

    @pytest.fixture
    def should_create_triggers(self) -> list[str]:
        return []

    @pytest.fixture
    def models(self, Base: type[DeclarativeBase]) -> None:
        class TextItem(Base):  # type: ignore[valid-type, misc]
            __tablename__ = "textitem"

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.String(255))

            search_vector: sa.Column[TSVectorType] = sa.Column(
                TSVectorType(auto_index=True)
            )

            content = sa.Column(sa.Text)
