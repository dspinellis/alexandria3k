-- Greek periodical ISSNs encountered and non-encountered in Crossref
-- Status|Number of ISSNs

CREATE TABLE rolap.joined_issns AS

WITH distinct_crossref_issns AS (
  SELECT DISTINCT issn FROM rolap.crossref_issns
),

distinct_lib_issns AS (
  SELECT DISTINCT issn FROM rolap.lib_issns
)

SELECT distinct_lib_issns.issn AS lib, distinct_crossref_issns.issn AS crossref
  FROM distinct_lib_issns
  FULL OUTER JOIN distinct_crossref_issns USING(issn)
  WHERE lib IS NOT null OR crossref IS NOT null;
