-- Greek periodical ISSNs encountered and non-encountered in Crossref
-- Status|Number of ISSNs

CREATE TABLE rolap.joined_issns AS

-- Map both ISSN types into one
WITH RECURSIVE all_crossref_issns AS (
  SELECT upper(issn_print) AS issn FROM works
  UNION
  SELECT upper(issn_electronic) AS issn FROM works
),

-- Use dash separator and remove duplicates
crossref_issns AS (
  SELECT Distinct substr(issn, 1, 4) || '-' || substr(issn, 5, 4) AS issn
    FROM all_crossref_issns
),

-- Split comma-separated ISSNs into rows
split_lib(id, issn, rest) AS (
    -- initial row
    SELECT
        id,
        TRIM(substr(issn || ',', 1, instr(issn || ',', ',') - 1)),
        TRIM(substr(issn || ',', instr(issn || ',', ',') + 1))
    FROM greek_periodicals

  UNION ALL

    SELECT
        id,
        TRIM(substr(rest, 1, instr(rest, ',') - 1)),
        TRIM(substr(rest, instr(rest, ',') + 1))
    FROM split_lib
    WHERE rest <> ''
),

normalized_lib AS (
  SELECT Distinct Upper(issn) AS issn FROM split_lib
)

SELECT lib_issns.issn AS lib, crossref_issns.issn AS crossref
  FROM normalized_lib AS lib_issns
  FULL OUTER JOIN crossref_issns USING(issn)
  WHERE lib IS NOT null OR crossref IS NOT null;
