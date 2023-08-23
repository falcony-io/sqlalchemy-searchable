import pytest
from sqlalchemy import text


class TestParse:
    @pytest.mark.parametrize(
        ("input", "output"),
        (
            ("", ""),
            ("()", ""),
            ("))someone(", "'someone':*"),
            ("((()))", ""),
            ("((    )) ( )", ""),
            ("))()()))))((((((  () ) (()  )))) (( )", ""),
            ("(((((((((((((())))))))))))))", ""),
            ('"" "())"")"(()"))""""', ""),
            ("()-()", ""),
            ("STAR", "'star':*"),
            ('""', ""),
            ("or or", "'or':* & 'or':*"),
            ("-or or", "!'or':* & 'or':*"),
            ("-or -or or", "!'or':* & !'or':* & 'or':*"),
            ("or", "'or':*"),
            ("star wars", "'star':* & 'wars':*"),
            ("star!#", "'star':*"),
            ("123.14 or 12a4", "'123.14':* | '12a4':*"),
            ("john@example.com", "'john@example.com':*"),
            ("star organs", "'star':* & 'organs':*"),
            ("organs", "'organs':*"),
            ("star or wars", "'star':* | 'wars':*"),
            ("star or or wars", "'star':* | 'or':*  & 'wars':*"),
            ('"star or or wars"', "star:* <-> or:* <-> or:* <-> wars:*"),
            ("star or   or    or    wars", "'star':* | 'or':* | 'wars':*"),
            ("star oror wars", "'star':* & 'oror':* & 'wars':*"),
            pytest.param(
                "star-wars",
                "'star-wars':* & 'star':* & 'wars':*",
                marks=pytest.mark.postgresql_max_version(13),
            ),
            pytest.param(
                "star-wars",
                "'star-wars':* <-> 'star':* <-> 'wars':*",
                marks=pytest.mark.postgresql_min_version(14),
            ),
            pytest.param(
                "star----wars",
                "'star':* & 'wars':*",
                marks=pytest.mark.postgresql_max_version(13),
            ),
            pytest.param(
                "star----wars",
                "'star':* <-> 'wars':*",
                marks=pytest.mark.postgresql_min_version(14),
            ),
            ("star   wars    luke", "'star':* & 'wars':* & 'luke':*"),
            ("örrimöykky", "'örrimöykky':*"),
            ("-star", "!'star':*"),
            ("--star", "!!'star':*"),
            ("star or or", "'star':* | or:*"),
            ('star or -""', "'star':*"),
            ('star or ""', "'star':*"),
            ("star or -", "'star':*"),
            ("star or (", "'star':*"),
            ("- -star", "!!'star':*"),
            ("star -wars", "'star':* & !'wars':*"),
            ("'star'", "'star':*"),
            ("''star''", "'star':*"),
            ('"star wars"', "'star':* <-> 'wars':*"),
            ('-"star wars"', "!( 'star':* <-> 'wars':* )"),
            ('""star wars""', "'star':* & 'wars':*"),
            ("star!:*@@?`", "'star':*"),
            ('"star', "'star':*"),
            ("ähtäri", "'ähtäri':*"),
            ('test"', "'test':*"),
            ('"test""', "'test':*"),
            (
                '"death star" -"star wars"',
                "'death':* <-> 'star':* & ! ('star':* <-> 'wars':*)",
            ),
            (
                '"something fishy happened"',
                "'something':* <-> 'fishy':* <-> 'happened':*",
            ),
            (
                '"star wars" "death star"',
                "'star':* <-> 'wars':* & 'death':* <-> 'star':*",
            ),
            (
                '"star wars""death star"',
                "'star':* <-> 'wars':* & 'death':* <-> 'star':*",
            ),
            ("star or wars luke or solo", "'star':* | 'wars':* & 'luke':* | 'solo':*"),
            pytest.param(
                "-star#wars",
                "!( 'star':* & 'wars':* )",
                marks=pytest.mark.postgresql_max_version(13),
            ),
            pytest.param(
                "-star#wars",
                "!( 'star':* <-> 'wars':* )",
                marks=pytest.mark.postgresql_min_version(14),
            ),
            pytest.param(
                "-star#wars or -star#wars",
                "!( 'star':* & 'wars':* ) | !( 'star':* & 'wars':* )",
                marks=pytest.mark.postgresql_max_version(13),
            ),
            pytest.param(
                "-star#wars or -star#wars",
                "!( 'star':* <-> 'wars':* ) | !( 'star':* <-> 'wars':* )",
                marks=pytest.mark.postgresql_min_version(14),
            ),
            pytest.param(
                '"star#wars star_wars"',
                "( 'star':* & 'wars':* ) <-> ( 'star':* & 'wars':* )",
                marks=pytest.mark.postgresql_max_version(13),
            ),
            pytest.param(
                '"star#wars star_wars"',
                "'star':* <-> 'wars':* <-> 'star':* <-> 'wars':*",
                marks=pytest.mark.postgresql_min_version(14),
            ),
        ),
    )
    def test_parse(self, session, input, output):
        assert (
            session.execute(
                text("SELECT parse_websearch('pg_catalog.simple', :input)"),
                {"input": input},
            ).scalar()
            == session.execute(
                text("SELECT CAST(:output AS tsquery)"), {"output": output}
            ).scalar()
        )
