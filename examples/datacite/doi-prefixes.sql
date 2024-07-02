-- List of DOI prefixes by number of works for each

SELECT SUBSTR(doi, 1, INSTR(doi, '/') - 1) AS prefix, Count(*) AS n
  FROM dc_works GROUP BY prefix ORDER BY n DESC;
