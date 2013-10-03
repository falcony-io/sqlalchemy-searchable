from sqlalchemy_searchable import parse_search_query
from sqlalchemy_searchable.parser import SearchQueryParser


class TestParseSearchQuery(object):
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

    def test_empty_string(self):
        parse_search_query('') == ''

    def test_hyphen_between_words(self):
        assert parse_search_query('star-wars') == 'star:* & wars:*'

    def test_or(self):
        assert parse_search_query('star or wars') == 'star:* | wars:*'

    def test_multiple_ors(self):
        assert parse_search_query('star or or or wars') == 'star:* | wars:*'

    def test_space_as_and(self):
        assert parse_search_query('star wars') == 'star:* & wars:*'

    def test_multiple_spaces_as_and(self):
        assert (
            parse_search_query('star   wars    luke') ==
            'star:* & wars:* & luke:*'
        )

    def test_and(self):
        assert parse_search_query('star and wars') == 'star:* & wars:*'

    def test_multiple_and(self):
        assert parse_search_query('star and and wars') == 'star:* & wars:*'

    def test_parenthesis(self):
        assert parse_search_query('(star wars) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_or_and(self):
        assert (
            parse_search_query('star or wars and luke or solo') ==
            'star:* | wars:* & luke:* | solo:*'
        )

    def test_empty_parenthesis(self):
        assert parse_search_query('()') == ''

    def test_nested_parenthesis(self):
        assert parse_search_query('((star wars)) or luke') == (
            '(star:* & wars:*) | luke:*'
        )

    def test_not(self):
        assert parse_search_query('-star') == (
            '! star:*'
        )

    def test_not_with_parenthesis(self):
        assert parse_search_query('-(star wars)') == '! (star:* & wars:*)'
