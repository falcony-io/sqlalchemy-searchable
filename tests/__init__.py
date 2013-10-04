# -*- coding: utf-8 -*-
import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.query import Query
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import make_searchable, SearchQueryMixin


engine = create_engine(
    'postgres://postgres@localhost/sqlalchemy_searchable_test'
)
Base = declarative_base()


class TestCase(object):
    def setup_method(self, method):
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()

        TextItem.__search_options__ = {
            'tablename': 'textitem',
            'search_vector_name': 'search_vector',
            'search_trigger_name': '{table}_search_update',
            'search_index_name': '{table}_search_index',
        }

    def teardown_method(self, method):
        self.session.close_all()
        Base.metadata.drop_all(engine)


make_searchable()


class TextItemQuery(Query, SearchQueryMixin):
    pass


class TextItem(Base):
    __search_options__ = {
        'tablename': 'textitem',
        'search_vector_name': 'search_vector',
        'search_trigger_name': '{table}_search_update',
        'search_index_name': '{table}_search_index',
    }
    __tablename__ = 'textitem'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    name = sa.Column(sa.Unicode(255))

    search_vector = sa.Column(TSVectorType('name', 'content'))

    content = sa.Column(sa.UnicodeText)


class Order(Base):
    __tablename__ = 'order'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Unicode(255))
    search_vector = sa.Column(TSVectorType('name'))


class Article(TextItem):
    __tablename__ = 'article'
    id = sa.Column(sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True)

    created_at = sa.Column(sa.DateTime)
