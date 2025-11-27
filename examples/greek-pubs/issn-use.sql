-- Greek periodical ISSNs encountered and non-encountered in Crossref
-- Status|Number of ISSNs

  SELECT 'Crossref ISSNs', Count(*) FROM joined_issns
    WHERE crossref IS NOT null
UNION ALL
  SELECT 'Library ISSNs', Count(*) FROM joined_issns
    WHERE lib IS NOT null
UNION ALL
  SELECT 'All ISSNs', Count(*) FROM joined_issns
UNION ALL
  SELECT 'Matched Crossref and library ISSNs', Count(*)
    FROM joined_issns WHERE lib IS NOT null AND crossref IS NOT null
UNION ALL
  SELECT 'Library ISSNs not in Crossref data', Count(*)
    FROM joined_issns WHERE crossref IS null
UNION ALL
  SELECT 'Crossref ISSNs not in library data', Count(*)
    FROM joined_issns WHERE lib IS null;
