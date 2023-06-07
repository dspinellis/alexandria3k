Python API examples
-------------------

After downloading the required data, the functionality of *alexandria3k*
can be accessed through its Python API, either interactively (for
exploratory data analytics) or through Python scripts (for long-running
jobs and for documenting research methods as repeatable processes).

Data source query and database population tasks are performed by
creating an object instance associated with the corresponding data
source class (e.g. `Crossref` or `Orcid`).
Although many of the examples are based on the Crossref data source, the
same principles apply to the other supported data sources.

Create a Crossref object
~~~~~~~~~~~~~~~~~~~~~~~~

Crossref functionality is accessed by means of a corresponding object
created by specifying the data directory.

.. code:: py

   from alexandria3k.data_sources.crossref import Crossref

   crossref_instance = Crossref('April 2022 Public Data File from Crossref')

You can also add a parameter indicating how to sample the containers.

.. code:: py

   from random import random, seed

   from alexandria3k.data_sources.crossref import Crossref

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

   from alexandria3k.data_sources.crossref import Crossref

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
records of authors identified in the Crossref publications through an
ORCID will be added.

.. code:: py

   from alexandria3k.data_sources.orcid import Orcid

   orcid_instance = Orcid("ORCID_2022_10_summaries.tar.gz")

   orcid_instance.populate(
       "database.db",
       columns=[
           "person_countries.*",
           "person_educations.orcid",
           "person_educations.organization_name",
       ],
       condition="""EXISTS (SELECT 1 FROM populated.work_authors
        WHERE work_authors.orcid = persons.orcid)"""
   )

.. _populate-the-database-with-journal-names-1:

Populate the database with journal names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k.data_sources.journal_names import JournalNames

   instance = JournalNames(
       "http://ftp.crossref.org/titlelist/titleFile.csv"
   )
   instance.populate("database.db")

.. _populate-the-database-with-funder-names-1:

Populate the database with funder names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k.data_sources.funder_names import FunderNames

   instance = FunderNames(
       "https://doi.crossref.org/funderNames?mode=list"
   )
   instance.populate("database.db")

.. _populate-the-database-with-data-regarding-open-access-journals-1:

Populate the database with data regarding open access journals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k.data_sources.doaj import Doaj

   instance = Doaj("https://doaj.org/csv")
   instance.populate("database.db")

.. _work-with-scopus-all-science-journal-classification-codes-asjc-1:

Work with Scopus All Science Journal Classification Codes (ASJC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k.data_sources.adjcs import Asjcs
   from alexandria3k.processes import link_works_asjcs

   # Populate database with ASJCs
   instance = Asjcs("resource:data/asjc.csv")
   instance.populate("database.db")

   # Link the (sometime previously populated works table) with ASJCs
   link_works_asjcs.process("database.db")

.. _populate-the-database-with-the-names-of-research-organizations-1:

Populate the database with the names of research organizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k.data_sources.ror import Ror

   instance = Ror("v1.17.1-2022-12-16-ror-data.zip")
   instance.populate("database.db")

.. _link-author-affiliations-with-research-organization-names-1:

Link author affiliations with research organization names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: py

   from alexandria3k import ror
   from alexandria3k.processes import link_aa_base_ror, link_aa_top_ror

   # Link affiliations with best match
   link_aa_base_ror.process("database.db")

   # Link affiliations with top parent of best match
   link_aa_top_ror.process("database.db")
