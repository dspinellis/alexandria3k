# Average number of work authors per decade

This is an example of a minimal _Alexandria3k_ application.
It [populates](./Makefile) a database with the publication year of works and
the work identifier of work authors from
a random sample specified to comprise about 0.02% of the Crossref containers.
It then creates a table named [num_work_authors.sql](./num_work_authors.sql)
with the number of authors per work, and, based on it,
runs a report named [authors-by-decade.sql ](./authors-by-decade.sql)
to list the average number of work authors per decade.

|Decade|Average number of authors|
|----|--------|
|1940|1.26190476190476|
|1950|1.79089790897909|
|1960|1.81883194278903|
|1970|2.37802907915994|
|1980|2.35445757250269|
|1990|2.62205387205387|
|2000|3.66545860050181|
|2010|3.7578125|
