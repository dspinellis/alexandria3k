-- Obtain work-record metrics not available from the graph

-- Do not use GROUP BY because the required sorted works table is stored
-- in memory (even with PRAGMA temp_store = FILE) and requires the allocation
-- of more than 1 GiB of memory.  This breaches the upper limit of memory
-- SQLite can allocate causing it to fail with the following error:
-- File "src/cursor.c", line 189, in resetcursor
-- apsw.FullError: database or disk is full

WITH counts AS (
  SELECT
    Count(*) AS total,
    SUM(CASE WHEN abstract is not null THEN 1 ELSE 0 END) AS abstract_count,

    SUM(CASE WHEN type = 'journal-article' THEN 1 ELSE 0 END) AS journal_article_count,
    SUM(CASE WHEN type = 'book-chapter' THEN 1 ELSE 0 END) AS book_chapter_count,
    SUM(CASE WHEN type = 'proceedings-article' THEN 1 ELSE 0 END) AS proceedings_article_count,
    SUM(CASE WHEN type = 'component' THEN 1 ELSE 0 END) AS component_count,
    SUM(CASE WHEN type = 'posted-content' THEN 1 ELSE 0 END) AS posted_content_count,
    SUM(CASE WHEN type = 'dataset' THEN 1 ELSE 0 END) AS dataset_count,
    SUM(CASE WHEN type = 'other' THEN 1 ELSE 0 END) AS other_count,
    SUM(CASE WHEN type = 'journal-issue' THEN 1 ELSE 0 END) AS journal_issue_count,
    SUM(CASE WHEN type = 'peer-review' THEN 1 ELSE 0 END) AS peer_review_count,
    SUM(CASE WHEN type = 'monograph' THEN 1 ELSE 0 END) AS monograph_count,
    SUM(CASE WHEN type = 'report' THEN 1 ELSE 0 END) AS report_count,
    SUM(CASE WHEN type = 'book' THEN 1 ELSE 0 END) AS book_count,
    SUM(CASE WHEN type = 'dissertation' THEN 1 ELSE 0 END) AS dissertation_count,
    SUM(CASE WHEN type = 'reference-entry' THEN 1 ELSE 0 END) AS reference_entry_count,
    SUM(CASE WHEN type = 'edited-book' THEN 1 ELSE 0 END) AS edited_book_count,
    SUM(CASE WHEN type = 'reference-book' THEN 1 ELSE 0 END) AS reference_book_count,
    SUM(CASE WHEN type = 'standard' THEN 1 ELSE 0 END) AS standard_count,
    SUM(CASE WHEN type = 'journal' THEN 1 ELSE 0 END) AS journal_count,
    SUM(CASE WHEN type = 'proceedings' THEN 1 ELSE 0 END) AS proceedings_count
  FROM works
)
SELECT 'total' AS name, total AS value FROM counts
UNION ALL
SELECT 'have-abstract' AS name, abstract_count AS value FROM counts
UNION ALL
SELECT 'journal-article' AS name, journal_article_count AS value FROM counts
UNION ALL
SELECT 'book-chapter' AS name, book_chapter_count AS value FROM counts
UNION ALL
SELECT 'proceedings-article' AS name, proceedings_article_count AS value FROM counts
UNION ALL
SELECT 'component' AS name, component_count AS value FROM counts
UNION ALL
SELECT 'posted-content' AS name, posted_content_count AS value FROM counts
UNION ALL
SELECT 'dataset' AS name, dataset_count AS value FROM counts
UNION ALL
SELECT 'other' AS name, other_count AS value FROM counts
UNION ALL
SELECT 'journal-issue' AS name, journal_issue_count AS value FROM counts
UNION ALL
SELECT 'peer-review' AS name, peer_review_count AS value FROM counts
UNION ALL
SELECT 'monograph' AS name, monograph_count AS value FROM counts
UNION ALL
SELECT 'report' AS name, report_count AS value FROM counts
UNION ALL
SELECT 'book' AS name, book_count AS value FROM counts
UNION ALL
SELECT 'dissertation' AS name, dissertation_count AS value FROM counts
UNION ALL
SELECT 'reference-entry' AS name, reference_entry_count AS value FROM counts
UNION ALL
SELECT 'edited-book' AS name, edited_book_count AS value FROM counts
UNION ALL
SELECT 'reference-book' AS name, reference_book_count AS value FROM counts
UNION ALL
SELECT 'standard' AS name, standard_count AS value FROM counts
UNION ALL
SELECT 'journal' AS name, journal_count AS value FROM counts
UNION ALL
SELECT 'proceedings' AS name, proceedings_count AS value FROM counts;
