ATTACH 'pubmed.db' as pubmed;
SELECT count(DISTINCT(pubmed_id)) from data join pubmed.pubmed_keywords on data.article_id = pubmed_keywords.article_id
WHERE pubmed_keywords.keyword like "SAS" 
-- or data.text match '"SAS"'
;
