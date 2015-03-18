import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import search
from tests import SchemaTestCase, TestCase


class TestMultipleSearchVectorsPerClass(SchemaTestCase):
    should_create_indexes = [
        u'ix_textitem_content_vector',
        u'ix_textitem_name_vector',
    ]
    should_create_triggers = [
        u'textitem_content_vector_trigger',
        u'textitem_name_vector_trigger',
    ]

    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))

            content = sa.Column(sa.UnicodeText)

            name_vector = sa.Column(TSVectorType('name'))

            content_vector = sa.Column(TSVectorType('content'))


class TestMultipleSearchVectorsSearchFunction(TestCase):
    def create_models(self):
        TestCase.create_models(self)

        class TextMultiItem(self.Base):
            __tablename__ = 'textmultiitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            name_vector = sa.Column(TSVectorType('name'))
            content_vector = sa.Column(TSVectorType('content'))

        self.TextMultiItem = TextMultiItem

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(
            self.TextMultiItem(name=u'index', content=u'lorem ipsum')
        )
        self.session.add(
            self.TextMultiItem(name=u'ipsum', content=u'admin content')
        )
        self.session.commit()

    def test_choose_vector(self):
        query = self.TextItemQuery(self.TextMultiItem, self.session)
        s1 = search(query, 'ipsum', vector=self.TextMultiItem.name_vector)
        assert s1.first().name == 'ipsum'
        s2 = search(query, 'ipsum', vector=self.TextMultiItem.content_vector)
        assert s2.first().name == 'index'
