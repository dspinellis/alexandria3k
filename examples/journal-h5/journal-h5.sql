.print create works_doi_idx
CREATE INDEX IF NOT EXISTS works_doi_idx ON works(doi);

.print create work_references_doi_idx
CREATE INDEX IF NOT EXISTS work_references_doi_idx ON work_references(doi);

.print create work_citations
CREATE TABLE IF NOT EXISTS work_citations AS
  SELECT doi, COUNT(*) AS citations_number
  FROM work_references
  GROUP BY doi;

.print create work_citations_doi_idx
CREATE INDEX IF NOT EXISTS work_citations_doi_idx ON work_citations(doi);

.print create works_issn
CREATE TABLE IF NOT EXISTS works_issn AS
  SELECT doi, Coalesce(works.issn_print, works.issn_electronic) AS issn
  FROM works WHERE issn is not null;

.print create issn_h5
CREATE TABLE IF NOT EXISTS issn_h5 AS
  WITH ranked_issn_citations AS (
    SELECT issn, citations_number,
      Row_number() OVER (
        PARTITION BY issn ORDER BY citations_number DESC) AS row_rank
    FROM work_citations
    INNER JOIN works_issn ON works_issn.doi = work_citations.doi
  ),
  eligible_ranks AS (
    SELECT issn, row_rank FROM ranked_issn_citations
    WHERE row_rank <= citations_number
  )
  SELECT issn, Max(row_rank) AS h5_index FROM eligible_ranks
  GROUP BY issn;

.print create h5 indices
CREATE INDEX IF NOT EXISTS issn_h5_issn_idx ON issn_h5(issn);
CREATE INDEX IF NOT EXISTS issn_h5_h5_index_idx ON issn_h5(h5_index);
CREATE INDEX IF NOT EXISTS journal_names_iss_print_idx
  ON journal_names(issn_print);
CREATE INDEX IF NOT EXISTS journal_names_iss_eprint_idx
  ON journal_names(issn_eprint);

.print Top-10 journal h5-index
.headers on
SELECT title, h5_index FROM issn_h5 LEFT JOIN journal_names
  ON issn_h5.issn = journal_names.issn_print
    OR issn_h5.issn = journal_names.issn_eprint
  ORDER BY h5_index DESC, title ASC
  LIMIT 20;
