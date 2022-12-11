SELECT Count(*), published_year,
  CASE
    -- Systematic reviews
    WHEN title LIKE '%systematic review%' THEN 'SY'
    WHEN title LIKE '%systematic literature review%' THEN 'SY'
    WHEN title LIKE '%systematic mapping study%' THEN 'SY'

    -- Unspecified secondary study
    WHEN title LIKE '%secondary study%' THEN 'S2'
    WHEN title LIKE '%literature survey%' THEN 'S2'
    WHEN title LIKE '%literature review%' THEN 'S2'

    WHEN title LIKE '%tertiary study%' THEN 'S3'

    -- Other synthesis methods
    WHEN title LIKE '%meta-analysis%' THEN 'MA'
    WHEN title LIKE '%bibliometric%' THEN 'BM'
    WHEN title LIKE '%scientometric%' THEN 'SM'
    WHEN title LIKE '%umbrella % review%' THEN 'UR'
    WHEN title LIKE '%mapping review%' THEN 'MR'
    ELSE null
  END AS study_type
  FROM works
  WHERE study_type is not null AND published_year is not null
  GROUP BY study_type, published_year
  ORDER BY study_type, published_year;
