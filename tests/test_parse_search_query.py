from sqlalchemy_searchable import parse_search_query
from sqlalchemy_searchable.parser import SearchQueryParser


class TestSafeSearchTerms(object):
    def test_uses_pgsql_wildcard_by_default(self):
        assert parse_search_query('star wars') == 'star:* & wars:*'

    def test_escapes_special_chars(self):
        assert parse_search_query('star!#') == 'star:*'

    def test_supports_custom_parsers(self):
        assert (
            parse_search_query(
                'star wars',
                parser=SearchQueryParser(wildcard='*')
            )
            ==
            'star* & wars*'
        )

    def test_operator_parsing(self):
        assert (
            parse_search_query('star or wars') ==
            'star:* | wars:*'
        )
