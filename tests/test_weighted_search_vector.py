import re

import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType

from sqlalchemy_searchable import search
from tests import SchemaTestCase, TestCase


class WeightedBase(object):
    def create_models(self):
        class WeightedTextItem(self.Base):
            __tablename__ = 'textitem'

            id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

            name = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            search_vector = sa.Column(
                TSVectorType(
                    'name',
                    'content',
                    weights={'name': 'A', 'content': 'B'}
                )
            )
        self.WeightedTextItem = WeightedTextItem


class TestCreateWeightedSearchVector(WeightedBase, SchemaTestCase):
    should_create_indexes = [u'ix_textitem_search_vector']
    should_create_triggers = [u'textitem_search_vector_trigger']

    def test_search_function_weights(self):
        func_name = 'textitem_search_vector_update'
        sql = """SELECT proname,prosrc FROM pg_proc
                 WHERE proname='{name}';"""
        name, src = self.session.execute(sql.format(name=func_name)).fetchone()
        pattern = (r"setweight\(to_tsvector\(.+?"
                   r"coalesce\(NEW.(\w+).+?"
                   r"\)\), '([A-D])'\)")
        first, second = (match.groups() for match in re.finditer(pattern, src))
        assert first == ('name', 'A')
        assert second == ('content', 'B')


class TestWeightedSearchFunction(WeightedBase, TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.session.add(
            self.WeightedTextItem(name=u'Gort', content=u'Klaatu barada nikto')
        )
        self.session.add(
            self.WeightedTextItem(name=u'Klaatu', content=u'barada nikto')
        )
        self.session.commit()

    def test_weighted_search_results(self):
        query = self.session.query(self.WeightedTextItem)
        first, second = search(query, 'klaatu', sort=True).all()
        assert first.search_vector == "'barada':2B 'klaatu':1A 'nikto':3B"
        assert (
            second.search_vector ==
            "'barada':3B 'gort':1A 'klaatu':2B 'nikto':4B"
        )
