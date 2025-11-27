-- Split the coma-separated library ISSNs into multiple normalized records.

CREATE TABLE rolap.lib_issns AS

WITH RECURSIVE split_lib(id, issn, rest) AS (
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
)
  SELECT DISTINCT id, Upper(issn) AS issn FROM split_lib;
