CREATE OR REPLACE FUNCTION parse_websearch(config regconfig, search_query text)
RETURNS tsquery AS $$
SELECT
    string_agg(
        (
            CASE
                WHEN position('''' IN words.word) > 0 THEN CONCAT(words.word, ':*')
                ELSE words.word
            END
        ),
        ' '
    )::tsquery
FROM (
    SELECT trim(
        regexp_split_to_table(
            websearch_to_tsquery(config, lower(search_query))::text,
            ' '
        )
    ) AS word
) AS words
$$ LANGUAGE SQL IMMUTABLE;


CREATE OR REPLACE FUNCTION parse_websearch(search_query text)
RETURNS tsquery AS $$
SELECT parse_websearch('pg_catalog.simple', search_query);
$$ LANGUAGE SQL IMMUTABLE;
