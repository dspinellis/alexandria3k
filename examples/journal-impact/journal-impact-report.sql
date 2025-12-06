-- Create a CSV file with the calculated 2-year and 5-year impact factors.

.mode csv
.headers on

SELECT
    journal_names.title,
    journal_names.publisher,
    journal_names.issn_print,
    journal_names.issn_eprint,
    journal_names.issns_additional,
    journal_names.doi,
    impact_factor2.citations_number AS citations_number2,
    impact_factor2.publications_number AS publications_number2,
    impact_factor2.impact_factor AS impact_factor2,
    impact_factor5.citations_number AS citations_number5,
    impact_factor5.publications_number AS publications_number5,
    impact_factor5.impact_factor AS impact_factor5,
    journal_h5.h5_index,
    journal_h5.h5_median
  FROM journal_names
  LEFT JOIN rolap.impact_factor2
    ON rolap.impact_factor2.journal_id =  journal_names.id
  LEFT JOIN rolap.impact_factor5
    ON rolap.impact_factor5.journal_id = journal_names.id
  LEFT JOIN rolap.journal_h5
    ON rolap.journal_h5.journal_id = journal_names.id
  ORDER BY title;
