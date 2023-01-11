-- Create a table with the number of each work's authors
CREATE TABLE rolap.num_work_authors AS
  SELECT work_authors.work_id, Count(*) AS num_authors
  FROM work_authors
  GROUP BY work_id;
