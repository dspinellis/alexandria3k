-- CREATE INDEX IF NOT EXISTS pubmed_abstracts_article_id_idx ON pubmed_abstracts(article_id);
-- CREATE INDEX IF NOT EXISTS pubmed_articles_id_idx ON pubmed_articles(id);
-- CREATE INDEX IF NOT EXISTS pubmed_keywords_article_id_idx ON pubmed_keywords(article_id);

CREATE VIRTUAL TABLE IF NOT EXISTS abstract_data USING fts5(article_id, text, title, completed_year, pubmed_id);
CREATE VIRTUAL TABLE IF NOT EXISTS keyword_data USING fts5(article_id, keyword);

INSERT INTO
    abstract_data(
        article_id,
        text,
        title,
        completed_year,
        pubmed_id
    )
SELECT
    ar.id,
    ab.text,
    ar.title,
    ar.completed_year,
    ar.pubmed_id
FROM
    main.pubmed_abstracts ab
    JOIN main.pubmed_articles ar ON ab.article_id = ar.id
WHERE
    completed_year IN (1997, 2007, 2017);

INSERT INTO
    keyword_data(article_id, keyword)
SELECT
    kw.article_id,
    kw.keyword
FROM
    main.pubmed_keywords kw
    JOIN main.pubmed_articles ar ON kw.article_id = ar.id
WHERE
    completed_year IN (1997, 2007, 2017);