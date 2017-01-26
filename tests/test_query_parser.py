# -*- coding: utf-8 -*-
from pyparsing import ParseException
from pytest import raises

from sqlalchemy_searchable.parser import SearchQueryParser


class TestSearchQueryParser(object):
    def setup_method(self, method):
        self.parser = SearchQueryParser()

    def test_unicode(self):
        assert self.parser.parse(u'안녕가は') == u'안녕가は:*'

    def test_empty_string(self):
        with raises(ParseException):
            self.parser.parse('')

    def test_or(self):
        assert self.parser.parse('star or wars') == 'star:* | wars:*'

    def test_multiple_ors(self):
        assert self.parser.parse('star or or or wars') == 'star:* | wars:*'

    def test_space_as_and(self):
        assert self.parser.parse('star wars') == 'star:* & wars:*'

    def test_multiple_spaces_as_and(self):
        assert (
            self.parser.parse('star   wars    luke') ==
            'star:* & wars:* & luke:*'
        )

    def test_parenthesis(self):
        assert self.parser.parse('(star wars) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_or_and(self):
        assert (
            self.parser.parse('star or wars   luke or solo') ==
            'star:* | wars:* & luke:* | solo:*'
        )

    def test_empty_parenthesis(self):
        with raises(ParseException):
            assert self.parser.parse('()')

    def test_nested_parenthesis(self):
        assert self.parser.parse('((star wars)) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_not(self):
        assert self.parser.parse('-star') == (
            '! star:*'
        )

    def test_not_with_parenthesis(self):
        assert self.parser.parse('-(star wars)') == '! (star:* & wars:*)'
