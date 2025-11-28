CREATE INDEX IF NOT EXISTS rolap.lib_issns_issn_idx ON lib_issns(issn);

CREATE TABLE rolap.cleaned_works AS

SELECT DISTINCT works.* FROM works
  LEFT JOIN rolap.lib_issns ON
    works.issn_print = lib_issns.issn
      OR works.issn_electronic = lib_issns.issn
  WHERE lib_issns.issn IS NOT null
    OR works.issn_print IS null AND works.issn_electronic IS null;
