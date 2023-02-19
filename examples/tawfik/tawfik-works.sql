-- Find works probably by (Dan) Tawfik

SELECT doi, given, family, published_year, issn_print
  FROM work_authors
  INNER JOIN works on work_authors.work_id = works.id
  WHERE family like 'tawfik' AND given LIKE 'd%';
