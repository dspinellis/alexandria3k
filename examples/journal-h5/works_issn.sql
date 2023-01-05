-- Create common electronic and print ISSN lookup

CREATE TABLE rolap.works_issn AS
  SELECT doi, Coalesce(works.issn_print, works.issn_electronic) AS issn
  FROM works WHERE issn is not null;
