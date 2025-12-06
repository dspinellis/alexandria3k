/*
 * Some journals, e.g. Nature Reviews Immunology are identified through
 * their additional ISSN (14741733)
 * In other cases the same ISSN appears as an additional one for older
 * names of the journal, e.g. 00284793 for
 * Boston Medical and Surgical Journal, The New England Journal of Medicine
 * and Surgery and the Collateral Branches of Science, The New-England Medical
 * Review and Journal, New England Journal of Medicine
 * Use only one record, starting from Print and ending in Additional
 */
CREATE TABLE rolap.impact_factor_titles AS
  WITH multiple_titles AS (
    SELECT impact_factor.issn, issn_type, title, impact_factor
      FROM rolap.impact_factor
      LEFT JOIN journals_issns
        ON impact_factor.issn = journals_issns.issn
      LEFT JOIN journal_names
        ON journals_issns.journal_id = journal_names.id
  ),
  prioritized_titles AS (
    SELECT *,
      Row_number() OVER (PARTITION BY issn ORDER BY issn_type DESC) AS priority
    FROM multiple_titles
  )
  SELECT issn, title, impact_factor FROM prioritized_titles
    WHERE priority = 1;
