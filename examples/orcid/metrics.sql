-- Output metrics of a fully-populated ORCID database

SELECT 'persons' AS type, (SELECT Count(*) FROM persons) AS records,
  (SELECT Count(DISTINCT orcid) FROM persons) AS persons UNION
SELECT 'researcher_urls' AS type, (SELECT Count(*) FROM person_researcher_urls) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_researcher_urls) AS persons UNION
SELECT 'countries' AS type, (SELECT Count(*) FROM person_countries) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_countries) AS persons UNION
SELECT 'keywords' AS type, (SELECT Count(*) FROM person_keywords) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_keywords) AS persons UNION
SELECT 'external_identifiers' AS type, (SELECT Count(*) FROM person_external_identifiers) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_external_identifiers) AS persons UNION
SELECT 'distinctions' AS type, (SELECT Count(*) FROM person_distinctions) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_distinctions) AS persons UNION
SELECT 'educations' AS type, (SELECT Count(*) FROM person_educations) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_educations) AS persons UNION
SELECT 'employments' AS type, (SELECT Count(*) FROM person_employments) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_employments) AS persons UNION
SELECT 'invited_positions' AS type, (SELECT Count(*) FROM person_invited_positions) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_invited_positions) AS persons UNION
SELECT 'memberships' AS type, (SELECT Count(*) FROM person_memberships) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_memberships) AS persons UNION
SELECT 'qualifications' AS type, (SELECT Count(*) FROM person_qualifications) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_qualifications) AS persons UNION
SELECT 'services' AS type, (SELECT Count(*) FROM person_services) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_services) AS persons UNION
SELECT 'fundings' AS type, (SELECT Count(*) FROM person_fundings) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_fundings) AS persons UNION
SELECT 'peer_reviews' AS type, (SELECT Count(*) FROM person_peer_reviews) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_peer_reviews) AS persons UNION
SELECT 'research_resources' AS type, (SELECT Count(*) FROM person_research_resources) AS records,
  (SELECT Count(DISTINCT person_id) FROM person_research_resources) AS persons;
