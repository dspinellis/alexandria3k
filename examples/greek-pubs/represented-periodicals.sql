-- Greek periodicals in Greek libraries included in Crossref
-- # Crossref articles|ISSN|title

WITH matched_issns AS (
  SELECT crossref AS issn
    FROM rolap.joined_issns WHERE lib IS NOT null AND crossref IS NOT null
),

matched_lib_issns AS (
  SELECT lib_issns.id, lib_issns.issn AS issn FROM matched_issns
  LEFT JOIN  rolap.lib_issns USING(issn)
),

matched_periodicals AS (
  SELECT id, matched_lib_issns.issn, title
    FROM greek_periodicals
    INNER JOIN matched_lib_issns USING(id)
),

counted_periodicals AS (
  SELECT Count(*) AS n, id, matched_periodicals.issn, title
    FROM matched_periodicals
    LEFT JOIN rolap.crossref_issns USING(issn)
    GROUP BY issn
)

SELECT n,
    group_concat(
      '<a href="https://portal.issn.org/resource/ISSN/' || issn || '">'
        || substr(issn, 1, 4) || '-' || substr(issn, 5, 4)
        || '</a>',
      ', '),
    title
  FROM counted_periodicals
  GROUP BY id
  ORDER BY n DESC;
