Command line execution examples
-------------------------------

After downloading the Crossref data, the functionality of *alexandria3k*
can be used through the corresponding command.
Below are isolated examples of command-line invocations
demonstrating particular aspects of *alexandria3k*.
You can find examples of complete proof-of-concept studies in the
`examples <https://github.com/dspinellis/alexandria3k/tree/main/examples>`__
directory.

Obtain list of command-line options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --help

Show DOI and title of all publications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
      --query 'SELECT DOI, title FROM works'

Save DOI and title of 2021 publications in a CSV file suitable for Excel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
     --query 'SELECT DOI, title FROM works WHERE published_year = 2021' \
     --output 2021.csv \
     --output-encoding use utf-8-sig

Count Crossref publications by year and type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This query performs a single pass through the data set to obtain the
number of Crossref publications by year and publication type.

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
      --query-file count-year-type.sql >results.csv

where ``count-year-type.sql`` contains:

.. code:: sql

   WITH counts AS (
     SELECT
       published_year AS year,
       type,
       Count(*) AS number
   FROM   works
       GROUP by published_year, type)

   SELECT year AS name, Sum(number) FROM counts
     GROUP BY year
   UNION
   SELECT type AS name, Sum(number) FROM counts
     GROUP BY type

Sampling
~~~~~~~~

The following command counts the number of publication that have or do
not have an abstract in an approximately 1% sample of the data set’s
containers. It uses a tab character (``\t``) to separate the output
fields. Through sampling the data containers it runs in a couple of
minutes, rather than hours.

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref'  \
      --sample 'random.random() < 0.01' \
      --field-separator $'\t' \
      --query-file count-no-abstract.sql

where ``count-no-abstract.sql`` contains:

.. code:: sql

   SELECT works.abstract is not null AS have_abstract, Count(*)
     FROM works GROUP BY have_abstract

For quick experiments, e.g. for verifying the queries of a full run,
consider sampling just three containers with
``--sample 'random.random() < 0.0002'``.

Database of COVID research
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command creates an SQLite database with all Crossref data
regarding publications that contain “COVID” in their title or abstract.

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
      --populate-db-path covid.db \
      --row-selection "title like '%COVID%' OR abstract like '%COVID%' "

Publications graph
~~~~~~~~~~~~~~~~~~

The following command selects only a subset of columns of the complete
Crossref data set to create a graph between navigable entities.

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
      --populate-db-path graph.db \
      --columns works.id works.doi works.published_year \
        work_references.work_id work_references.doi work_references.isbn \
        work_funders.id work_funders.work_id work_funders.doi \
        funder_awards.funder_id funder_awards.name \
        author_affiliations.author_id author_affiliations.name \
        work_links.work_id work_subjects.work_id work_subjects.name \
        work_authors.id work_authors.work_id work_authors.orcid

Through this data set you can run on the database queries such as the
following.

.. code:: sql

   SELECT COUNT(*) FROM works;
   SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM works_subjects);
   SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM work_references);
   SELECT COUNT(*) FROM affiliations_works;
   SELECT COUNT(*) FROM (SELECT DISTINCT work_id FROM work_funders);

   SELECT COUNT(*) FROM work_authors;
   SELECT COUNT(*) FROM work_authors WHERE orcid is not null;
   SELECT COUNT(*) FROM (SELECT DISTINCT orcid FROM work_authors);

   SELECT COUNT(*) FROM authors_affiliations;
   SELECT COUNT(*) FROM affiliation_names;

   SELECT COUNT(*) FROM works_subjects;
   SELECT COUNT(*) FROM subject_names;

   SELECT COUNT(*) FROM work_funders;
   SELECT COUNT(*) FROM funder_awards;

   SELECT COUNT(*) FROM work_references;

Record selection from external database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command creates an SQLite database with all Crossref data
of works whose DOI appears in the attached database named
``selected.db``.

.. code:: sh

   alexandria3k --data-source Crossref 'April 2022 Public Data File from Crossref' \
      --populate-db-path selected-works.db \
      --attach-databases 'attached:selected.db' \
      --row-selection "EXISTS (SELECT 1 FROM attached.selected_dois WHERE works.doi = selected_dois.doi)"

Populate the database with author records from ORCID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Only records of authors identified in the publications through an ORCID
will be added.

.. code:: sh

   alexandria3k --populate-db-path database.db \
     --data-source ORCID ORCID_2022_10_summaries.tar.gz \
     --linked-records persons

Populate the database with journal names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --populate-db-path database.db \
     --data-source journal-names http://ftp.crossref.org/titlelist/titleFile.csv

Populate the database with funder names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --populate-db-path database.db \
     --data-source funder-names https://doi.crossref.org/funderNames?mode=list

Work with Scopus All Science Journal Classification Codes (ASJC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   # Populate database with ASJCs
   alexandria3k --populate-db-path database.db --data-source ASJC

   # Link the (sometime previously populated works table) with ASJCs
   alexandria3k --populate-db-path database.db --execute link-works-asjcs

Populate the database with data regarding open access journals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   alexandria3k --populate-db-path database.db \
     --data-source DOAJ https://doaj.org/csv

Populate the database with the names of research organizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Populate the research organization registry (ROR) tables.

.. code:: sh

   # Fetch the ROR data file (~21 MB)
   wget -O ror-v1.17.1.zip \
     "https://zenodo.org/record/7448410/files/v1.17.1-2022-12-16-ror-data.zip?download=1"

   # Populate the database
   alexandria3k --populate-db-path database.db \
     --data-source ROR ror-v1.17.1.zip

Link author affiliations with research organization names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given a database already populated with work author affiliations and the
research organization registry fill-in the table ``work_authors_rors``
linking the two.

.. code:: sh

   # Link affiliations with best match
   alexandria3k --populate-db-path database.db --execute link-aa-base-ror

   # Link affiliations with top parent of best match
   alexandria3k --populate-db-path database.db --execute link-aa-top-ror

After linking, the results’ quality can be verified with queries such as
the following.

.. code:: sql

   -- Display affiliation matches
   SELECT author_affiliations.name, research_organizations.name FROM
     work_authors
     INNER JOIN author_affiliations
       ON work_authors.id = author_affiliations.author_id
     INNER JOIN work_authors_rors
       ON work_authors_rors.work_author_id = work_authors.id
     INNER JOIN research_organizations
       ON research_organizations.id = work_authors_rors.ror_id;

   -- Display unmatched affiliations
   SELECT author_affiliations.name FROM
     work_authors
     INNER JOIN author_affiliations
       ON work_authors.id = author_affiliations.author_id
     LEFT JOIN work_authors_rors
       ON work_authors_rors.work_author_id = work_authors.id
     WHERE work_authors_rors.ror_id is null;
