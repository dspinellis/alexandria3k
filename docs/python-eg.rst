Python API examples
-------------------

After downloading the Crossref data, the functionality of *alexandria3k*
can be accessed through its Python API, either interactively (for
exploratory data analytics) or through Python scripts (for long-running
jobs and for documenting research methods as repeatable processes).

Create a Crossref object
~~~~~~~~~~~~~~~~~~~~~~~~

Crossref functionality is accessed by means of a corresponding object
created by specifying the data directory.

.. code:: py

   from alexandria3k.crossref import Crossref

   crossref_instance = Crossref('April 2022 Public Data File from Crossref')

You can also add a parameter indicating how to sample the containers.

.. code:: py

   from random import random, seed

   from alexandria3k.crossref import Crossref

   # Randomly (but deterministically) sample 1% of the containers
   seed("alexandria3k")
   crossref_instance = Crossref('April 2022 Public Data File from Crossref',
     lambda _name: random() < 0.01)

Iterate through the DOI and title of all publications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   for (doi, title) in crossref_instance.query('SELECT DOI, title FROM works'):
       print(doi, title)

Create a dictionary of which 2021 publications were funded by each body
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here ``partition=True`` is passed to the ``query`` method in order to
have the query run separately (and therefore efficiently) on each
Crossref data container.

.. code:: py

   from collections import defaultdict

   works_by_funder = defaultdict(list)

   for (funder_doi, work_doi) in crossref_instance.query(
       """
      SELECT work_funders.doi, works.doi FROM works
          INNER JOIN work_funders on work_funders.work_id = works.id
          WHERE published_year = 2021
       """,
       partition=True,
   ):
       works_by_funder[funder_doi].append(work_doi)

.. _database-of-covid-research-1:

Database of COVID research
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following command creates an SQLite database with all Crossref data
regarding publications that contain “COVID” in their title or abstract.

.. code:: py

   crossref_instance.populate(
       "covid.db", condition="title like '%COVID%' OR abstract like '%COVID%'"
   )

Reference graph
~~~~~~~~~~~~~~~

The following command populates an SQLite database by selecting only a
subset of columns of the complete Crossref data set to create a
navigable graph between publications and their references.

.. code:: py

   crossref_instance.populate(
       "references.db",
       columns=[
           "works.id",
           "works.doi",
           "work_references.work_id",
           "work_references.doi",
       ],
       condition="work_references.doi is not null",
   )

.. _record-selection-from-external-database-1:

Record selection from external database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following commands create an SQLite database with all Crossref data
of works whose DOI appears in the attached database named
``selected.db``.

.. code:: py

   from alexandria3k.crossref import Crossref

   crossref_instance = Crossref(
        'April 2022 Public Data File from Crossref',
       attach_databases=["attached:selected.db"]
   )

   crossref_instance.populate(
       "selected-works.db",
       condition="EXISTS (SELECT 1 FROM attached.selected_dois WHERE works.doi = selected_dois.doi)"
   )

Populate the database from ORCID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add tables containing author country and education organization. Only
records of authors identified in the publications through an ORCID will
be added.

.. code:: py

   from alexandria3k import orcid

   orcid.populate(
       "database.db",
       "ORCID_2022_10_summaries.tar.gz",
       columns=[
           "person_countries.*",
           "person_educations.orcid",
           "person_educations.organization_name",
       ],
       authors_only=True,
       works_only=False
   )

.. _populate-the-database-with-journal-names-1:

Populate the database with journal names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import csv_sources

   csv_sources.populate_journal_names(
       "database.db",
       "http://ftp.crossref.org/titlelist/titleFile.csv"
   )

.. _populate-the-database-with-funder-names-1:

Populate the database with funder names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import csv_sources

   csv_sources.populate_funder_names(
       "database.db",
       "https://doi.crossref.org/funderNames?mode=list"
   )

.. _populate-the-database-with-data-regarding-open-access-journals-1:

Populate the database with data regarding open access journals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import csv_sources

   csv_sources.populate_open_access_journals(
       "database.db",
       "https://doaj.org/csv"
   )

.. _work-with-scopus-all-science-journal-classification-codes-asjc-1:

Work with Scopus All Science Journal Classification Codes (ASJC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import csv_sources

   # Populate database with ASJCs
   csv_sources.populate_asjc("database.db", "resource:data/asjc.csv")

   # Link the (sometime previously populated works table) with ASJCs
   csv_sources.link_works_asjcs("database.db")

.. _populate-the-database-with-the-names-of-research-organizations-1:

Populate the database with the names of research organizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import ror

   ror.populate(
       "v1.17.1-2022-12-16-ror-data.zip",
       "database.db"
   )

.. _link-author-affiliations-with-research-organization-names-1:

Link author affiliations with research organization names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import ror

   # Link affiliations with best match
   ror.link_author_affiliations(args.populate_db_path, link_to_top=False)

   # Link affiliations with top parent of best match
   ror.link_author_affiliations(args.populate_db_path, link_to_top=True)


