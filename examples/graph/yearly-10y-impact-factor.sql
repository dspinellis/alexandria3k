-- Global ten-year impact factor

SELECT ten_year_citations.year,
  Cast(citations_number AS float) / ten_year_publications.n AS impact_factor
  FROM rolap.ten_year_citations
  INNER JOIN rolap.ten_year_publications
    ON ten_year_publications.year = ten_year_citations.year;
