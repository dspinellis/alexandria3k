-- Show the values used in the employed DataCite schemes

SELECT 'dc_work_funding_references.funder_identifier_type' AS field, funder_identifier_type AS name, Count(*) AS value FROM dc_work_funding_references GROUP BY funder_identifier_type UNION

SELECT 'dc_works.identifier_type' AS field, identifier_type AS name, Count(*) AS value FROM dc_works GROUP BY identifier_type UNION

SELECT 'dc_work_creators.name_type' AS field, name_type AS name, Count(*) AS value FROM dc_work_creators GROUP BY name_type UNION

SELECT 'dc_creator_name_identifiers.scheme_uri' AS field, scheme_uri AS name, Count(*) AS value FROM dc_creator_name_identifiers GROUP BY scheme_uri UNION

SELECT 'dc_work_contributors.contributor_type' AS field, contributor_type AS name, Count(*) AS value FROM dc_work_contributors GROUP BY contributor_type UNION

SELECT 'dc_contributor_name_identifiers.name_identifier_scheme' AS field, name_identifier_scheme AS name, Count(*) AS value FROM dc_contributor_name_identifiers GROUP BY name_identifier_scheme UNION

SELECT 'dc_work_titles.title_type' AS field, title_type AS name, Count(*) AS value FROM dc_work_titles GROUP BY title_type UNION

SELECT 'dc_work_subjects.subject_scheme' AS field, subject_scheme AS name, Count(*) AS value FROM dc_work_subjects GROUP BY subject_scheme UNION

SELECT 'dc_work_subjects.value_uri' AS field, value_uri AS name, Count(*) AS value FROM dc_work_subjects GROUP BY value_uri UNION

SELECT 'dc_work_dates.date_type' AS field, date_type AS name, Count(*) AS value FROM dc_work_dates GROUP BY date_type UNION

SELECT 'dc_work_related_identifiers.related_identifier_type' AS field, related_identifier_type AS name, Count(*) AS value FROM dc_work_related_identifiers GROUP BY related_identifier_type UNION

SELECT 'dc_work_related_identifiers.relation_type' AS field, relation_type AS name, Count(*) AS value FROM dc_work_related_identifiers GROUP BY relation_type UNION

SELECT 'dc_work_related_identifiers.scheme_type' AS field, scheme_type AS name, Count(*) AS value FROM dc_work_related_identifiers GROUP BY scheme_type UNION

SELECT 'dc_work_rights.rights_identifier_scheme' AS field, rights_identifier_scheme AS name, Count(*) AS value FROM dc_work_rights GROUP BY rights_identifier_scheme UNION

SELECT 'dc_work_rights.rights_identifier' AS field, rights_identifier AS name, Count(*) AS value FROM dc_work_rights GROUP BY rights_identifier UNION

SELECT 'dc_work_descriptions.description_type' AS field, description_type AS name, Count(*) AS value FROM dc_work_descriptions GROUP BY description_type UNION

SELECT 'dc_work_funding_references.funder_identifier_type' AS field, funder_identifier_type AS name, Count(*) AS value FROM dc_work_funding_references GROUP BY funder_identifier_type;
