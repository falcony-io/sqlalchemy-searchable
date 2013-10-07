import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from tests import SchemaTestCase


class TestMultipleSearchVectorsPerClass(SchemaTestCase):
    should_create_indexes = [
        u'textitem_name_vector_index',
        u'textitem_content_vector_index'
    ]
    should_create_triggers = [
        u'textitem_name_vector_trigger',
        u'textitem_content_vector_trigger'
    ]

    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            content = sa.Column(sa.UnicodeText)

            name_vector = sa.Column(TSVectorType('name'))

            content_vector = sa.Column(TSVectorType('content'))
