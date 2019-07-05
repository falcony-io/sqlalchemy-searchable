# -*- coding: utf-8 -*-
import pytest

from tests import TestCase


class TestParse(TestCase):
    @pytest.mark.parametrize(
        ('input', 'output'),
        (
            ('', ''),
            ('()', ''),
            ('))someone(', "'someone':*"),
            ('((()))', ''),
            ('((    )) ( )', ''),
            ('))()()))))((((((  () ) (()  )))) (( )', ''),
            ('(((((((((((((())))))))))))))', ''),
            ('"" "())"")"(()"))""""', ''),
            ('()-()', ''),
            ('STAR', "'star':*"),
            ('""', ''),
            ('or or', ''),
            ('-or or', ''),
            ('-or -or or', ''),
            ('or', ''),
            ('"or"', "'or'"),
            ('star"wars"', "'wars' & 'star':*"),
            ('star wars', "'star':* & 'wars':*"),
            ('star!#', "'star':*"),
            ('123.14 or 12a4', "'123.14':* | '12a4':*"),
            ('john@example.com', "'john@example.com':*"),
            ('star organs', "'star':* & 'organs':*"),
            ('organs', "'organs':*"),
            ('star or wars', "'star':* | 'wars':*"),
            ('star or or wars', "'star':* | 'wars':*"),
            ('"star or or wars"', "star <-> or <-> or <-> wars"),
            ('star or   or    or    wars', "'star':* | 'wars':*"),
            ('star oror wars', "'star':* & 'oror':* & 'wars':*"),
            ('star-wars', "'star-wars':* & 'star':* & 'wars':*"),
            ('star----wars', "'star':* & 'wars':*"),
            ('star   wars    luke', "'star':* & 'wars':* & 'luke':*"),
            ('(star wars) or luke', "'star':* & 'wars':* | 'luke':*"),
            ('örrimöykky', "'örrimöykky':*"),
            ('-star', "!'star':*"),
            ('--star', "!'star':*"),
            ('star or or', "'star':*"),
            ('star or -""', "'star':*"),
            ('star or ""', "'star':*"),
            ('star or -', "'star':*"),
            ('star or (', "'star':*"),
            ('---------star', "!'star':*"),
            ('- -- ---- --star', "!'star':*"),
            ('star -wars', "'star':* & !'wars':*"),
            ('-(star wars)', "!( 'star':* & 'wars':* )"),
            ('---(star wars)', "!( 'star':* & 'wars':* )"),
            ("'star'", "'star':*"),
            ("''star''", "'star':*"),
            ('"star wars"', "'star' <-> 'wars'"),
            ('-"star wars"', "!( 'star' <-> 'wars' )"),
            ('""star wars""', "'star':* & 'wars':*"),
            ('star!:*@@?`', "'star':*"),
            ('"star', "'star':*"),
            ('ähtäri', "'ähtäri':*"),
            ('test"', "'test':*"),
            ('"test""', "'test'"),
            (
                '"death star" -"star wars"',
                "'death' <-> 'star' & ! ('star' <-> 'wars')"
            ),
            ('((star wars)) or luke', "'star':* & 'wars':* | 'luke':*"),
            (
                '"something fishy happened"',
                "'something' <-> 'fishy' <-> 'happened'"
            ),
            (
                '"star wars" "death star"',
                "'star' <-> 'wars' & 'death' <-> 'star'"
            ),
            (
                '"star wars""death star"',
                "'star' <-> 'wars' & 'death' <-> 'star'"
            ),
            (
                'star or wars luke or solo',
                "'star':* | 'wars':* & 'luke':* | 'solo':*"
            ),
        )
    )
    def test_parse(self, input, output):
        assert (
            self.session.execute(
                "SELECT tsq_parse('pg_catalog.simple', :input)",
                {'input': input}
            ).scalar() ==
            self.session.execute(
                "SELECT CAST(:output AS tsquery)", {'output': output}
            ).scalar()
        )


class TestArrayNremove(TestCase):
    @pytest.mark.parametrize(
        ('original', 'element', 'count', 'output'),
        (
            ([], 1, 1, []),
            ([1], 1, 1, []),
            ([1, 2, 2, 4], 2, 1, [1, 2, 4]),
            ([1, 2, 2, 4], 2, 2, [1, 4]),
            ([1, 2, 2, 4], 2, 0, [1, 2, 2, 4]),
            ([1, 2, 2, 4], 3, 1, [1, 2, 2, 4]),
            (['a', 'b', 'c'], 'b', 1, ['a', 'c']),
            (['a', 'b', 'c', 'a'], 'a', -1, ['a', 'b', 'c']),
            (['a', 'b', 'a', 'c', 'a'], 'a', -2, ['a', 'b', 'c']),
        )
    )
    def test_array_nremove(self, original, element, count, output):
        assert (
            self.session.execute(
                """SELECT array_nremove(:original, :element, :count)""",
                {
                    'original': original,
                    'element': element,
                    'count': count
                }
            ).scalar() == output
        )
