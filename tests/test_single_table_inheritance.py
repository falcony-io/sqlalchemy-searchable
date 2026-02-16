from datetime import datetime

import pytest
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_utils import TSVectorType

from tests.schema_test_case import SchemaTestCase


class TestSearchableWithSingleTableInheritance(SchemaTestCase):
    @pytest.fixture
    def should_create_indexes(self) -> list[str]:
        return ["ix_textitem_search_vector"]

    @pytest.fixture
    def should_create_triggers(self) -> list[str]:
        return ["textitem_search_vector_trigger"]

    @pytest.fixture
    def models(self, Base: type[DeclarativeBase]) -> None:
        class TextItem(Base):  # type: ignore[valid-type, misc]
            __tablename__ = "textitem"

            id: Mapped[int] = mapped_column(primary_key=True)

            name: Mapped[str]

            search_vector: Mapped[TSVectorType] = mapped_column(
                TSVectorType("name", "content")
            )

            content: Mapped[str]

        class Article(TextItem):
            created_at: Mapped[datetime | None]
