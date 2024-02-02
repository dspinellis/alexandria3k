CREATE INDEX IF NOT EXISTS pubmed_abstracts_article_id_idx ON pubmed_abstracts(article_id);
CREATE INDEX IF NOT EXISTS pubmed_articles_id_idx ON pubmed_articles(id);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_abstracts USING fts5(article_id, text, title, year, pubmed_id);

INSERT INTO
    fts_abstracts(
        article_id,
        text,
        title,
        year,
        pubmed_id
    )
SELECT
    ar.id,
    ab.text,
    ar.title,
    COALESCE(ar.completed_year, ar.journal_year),
    ar.pubmed_id
FROM
    main.pubmed_abstracts ab
    JOIN main.pubmed_articles ar ON ab.article_id = ar.id
WHERE
    COALESCE(completed_year, journal_year) IN (1997, 2007, 2017);
