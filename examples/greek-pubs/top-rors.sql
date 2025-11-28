-- Top ten author research organizations
-- Organization name|Authorships
CREATE INDEX IF NOT EXISTS work_authors_work_id_idx ON work_authors(work_id);

CREATE INDEX IF NOT EXISTS work_authors_rors_work_author_id_idx
  ON work_authors_rors(work_author_id);

SELECT  ror.name, Count(*) FROM work_authors_rors AS war
  LEFT JOIN work_authors ON war.work_author_id = work_authors.id
  INNER JOIN rolap.cleaned_works ON cleaned_works.id = work_authors.work_id
  LEFT JOIN research_organizations AS ror ON war.ror_id = ror.id
  GROUP BY ror.id
  ORDER BY Count(*) DESC
  LIMIT 10;
