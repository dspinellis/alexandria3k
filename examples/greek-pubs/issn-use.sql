-- Matches between Greek library periodical ISSNs and Crossref
-- Status|Number of ISSNs

SELECT 'Crossref ISSNs', Count(*)
  FROM rolap.joined_issns
  WHERE crossref IS NOT null
UNION ALL SELECT 'Greek library Greek ISSNs', Count(*)
  FROM rolap.joined_issns
  WHERE lib IS NOT null
UNION ALL SELECT 'All ISSNs', Count(*)
  FROM rolap.joined_issns
UNION ALL SELECT 'Matched Crossref and Greek library ISSNs', Count(*)
  FROM rolap.joined_issns WHERE lib IS NOT null AND crossref IS NOT null
UNION ALL SELECT 'Greek library ISSNs not in Crossref data', Count(*)
  FROM rolap.joined_issns WHERE crossref IS null
UNION ALL SELECT 'Crossref ISSNs not in Greek library data', Count(*)
  FROM rolap.joined_issns WHERE lib IS null;
