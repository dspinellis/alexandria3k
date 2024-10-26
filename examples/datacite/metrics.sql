-- Output metrics of a fully-populated DataCite database

SELECT 'works' AS type,
  (SELECT Count(*) FROM dc_works) AS records UNION
SELECT 'work_rights' AS type,
  (SELECT Count(*) FROM dc_work_rights) AS records UNION
SELECT 'creator_name_identifiers' AS type,
  (SELECT Count(*) FROM dc_creator_name_identifiers) AS records UNION
SELECT 'work_creators' AS type,
  (SELECT Count(*) FROM dc_work_creators) AS records UNION
SELECT 'work_titles' AS type,
  (SELECT Count(*) FROM dc_work_titles) AS records UNION
SELECT 'creator_affiliations' AS type,
  (SELECT Count(*) FROM dc_creator_affiliations) AS records UNION
SELECT 'work_funding_references' AS type,
  (SELECT Count(*) FROM dc_work_funding_references) AS records UNION
SELECT 'work_geo_locations' AS type,
  (SELECT Count(*) FROM dc_work_geo_locations) AS records UNION
SELECT 'work_dates' AS type,
  (SELECT Count(*) FROM dc_work_dates) AS records UNION
SELECT 'work_contributors' AS type,
  (SELECT Count(*) FROM dc_work_contributors) AS records UNION
SELECT 'contributor_affiliations' AS type,
  (SELECT Count(*) FROM dc_contributor_affiliations) AS records UNION
SELECT 'work_related_identifiers' AS type,
  (SELECT Count(*) FROM dc_work_related_identifiers) AS records UNION
SELECT 'contributor_name_identifiers' AS type,
  (SELECT Count(*) FROM dc_contributor_name_identifiers) AS records UNION
SELECT 'work_subjects' AS type,
  (SELECT Count(*) FROM dc_work_subjects) AS records UNION
SELECT 'work_descriptions' AS type,
  (SELECT Count(*) FROM dc_work_descriptions) AS records;
