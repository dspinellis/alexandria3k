SELECT 'Organizations' AS name, Count(*) FROM research_organizations
UNION
SELECT 'Aliases' AS name,   Count(*) from ror_aliases
UNION
SELECT 'Acronyms' AS name,   Count(*) from ror_acronyms
UNION
SELECT 'Relationships' AS name,   Count(*) from ror_relationships;
