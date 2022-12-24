-- Display metrics of a fully-populated ORCID database

SELECT "persons" AS type, (SELECT COUNT(*) FROM persons) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT orcid FROM persons)) AS persons UNION
SELECT "researcher_urls" AS type, (SELECT COUNT(*) FROM researcher_urls) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM researcher_urls)) AS persons UNION
SELECT "person_countries" AS type, (SELECT COUNT(*) FROM person_countries) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM person_countries)) AS persons UNION
SELECT "person_keywords" AS type, (SELECT COUNT(*) FROM person_keywords) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM person_keywords)) AS persons UNION
SELECT "person_external_identifiers" AS type, (SELECT COUNT(*) FROM person_external_identifiers) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM person_external_identifiers)) AS persons UNION
SELECT "distinctions" AS type, (SELECT COUNT(*) FROM distinctions) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM distinctions)) AS persons UNION
SELECT "educations" AS type, (SELECT COUNT(*) FROM educations) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM educations)) AS persons UNION
SELECT "employments" AS type, (SELECT COUNT(*) FROM employments) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM employments)) AS persons UNION
SELECT "invited_positions" AS type, (SELECT COUNT(*) FROM invited_positions) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM invited_positions)) AS persons UNION
SELECT "memberships" AS type, (SELECT COUNT(*) FROM memberships) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM memberships)) AS persons UNION
SELECT "qualifications" AS type, (SELECT COUNT(*) FROM qualifications) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM qualifications)) AS persons UNION
SELECT "services" AS type, (SELECT COUNT(*) FROM services) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM services)) AS persons UNION
SELECT "fundings" AS type, (SELECT COUNT(*) FROM fundings) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM fundings)) AS persons UNION
SELECT "peer_reviews" AS type, (SELECT COUNT(*) FROM peer_reviews) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM peer_reviews)) AS persons UNION
SELECT "research_resources" AS type, (SELECT COUNT(*) FROM research_resources) AS records,
  (SELECT COUNT(*) FROM (SELECT DISTINCT person_id FROM research_resources)) AS persons;
