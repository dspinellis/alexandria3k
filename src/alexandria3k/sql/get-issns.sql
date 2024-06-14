SELECT DISTINCT COALESCE(issn_print, issn_electronic) AS issn
FROM works
WHERE issn IS NOT NULL