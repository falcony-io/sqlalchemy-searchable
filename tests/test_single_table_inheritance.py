import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from tests import SchemaTestCase


class TestSearchableWithSingleTableInheritance(SchemaTestCase):
    should_create_indexes = [
        u'ix_textitem_search_vector',
    ]
    should_create_triggers = [
        u'textitem_search_vector_trigger',
    ]

    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            search_vector = sa.Column(TSVectorType('name', 'content'))

            content = sa.Column(sa.UnicodeText)

        class Article(TextItem):
            created_at = sa.Column(sa.DateTime)
