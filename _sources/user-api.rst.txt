Python user API
===============

.. Automatically generated file. Do not modify by hand.

Data sources
~~~~~~~~~~~~

The *alexandria3k* data sources can be used to populate an SQLite database
or to run SQL queries directly on their data.
All are available through the classes documented below.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   asjcs
   crossref
   doaj
   funder_names
   journal_names
   orcid
   ror
   uspto


Data processing operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

The *alexandria3k* data processing modules operate on previously
populated SQLite databases.
They process existing elements and generate new tables performing
tasks such as normalization and disambiguation.
All are available through the modules documented below.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   link_aa_base_ror
   link_aa_top_ror
   link_uspto_doi
   link_works_asjcs
