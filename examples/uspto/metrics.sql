-- Output metrics of a fully-populated USPTO database

SELECT 'patents' AS type, (SELECT Count(*) FROM us_patents) AS records UNION
SELECT 'inventors' AS type, (SELECT Count(*) FROM usp_inventors) AS records UNION
SELECT 'applicants' AS type, (SELECT Count(*) FROM usp_applicants) AS records UNION
SELECT 'icpr_classifications' AS type, (SELECT Count(*) FROM usp_icpr_classifications) AS records UNION
SELECT 'cpc_classifications' AS type, (SELECT Count(*) FROM usp_cpc_classifications) AS records UNION
SELECT 'related_documents' AS type, (SELECT Count(*) FROM usp_related_documents) AS records UNION
SELECT 'field_of_classification' AS type, (SELECT Count(*) FROM usp_field_of_classification) AS records UNION
SELECT 'agents' AS type, (SELECT Count(*) FROM usp_agents) AS records UNION
SELECT 'assignees' AS type, (SELECT Count(*) FROM usp_assignees) AS records UNION
SELECT 'citations' AS type, (SELECT Count(*) FROM usp_citations) AS records UNION
SELECT 'patent_family' AS type, (SELECT Count(*) FROM usp_patent_family) AS records;
