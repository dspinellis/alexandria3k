-- Top ten most-referenced articles
-- References|DOI|Title

SELECT References_count, DOI, Title
  FROM works
  ORDER BY references_count DESC
  LIMIT 10;
