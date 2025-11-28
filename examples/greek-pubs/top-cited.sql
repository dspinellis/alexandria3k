-- Top ten most-referenced articles
-- References|DOI|Title

SELECT References_count, DOI, Title
  FROM rolap.cleaned_works AS works
  ORDER BY references_count DESC
  LIMIT 10;
