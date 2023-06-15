Schema diagrams
---------------

The complete schema of a fully-populated database appears below.
Opening the image in a separate window will allow you to zoom it.

.. figure:: ./schema/all.svg
   :alt: Complete data schema

In addition,
direct SQL queries can be performed on each data source's tables.
Queries involving multiple scans of the tables (e.g. relational joins)
should be performed by directing *alexandria3k* to perform them
separately in each partition. This however means that aggregation
operations will not work as expected, because they will be run multiple
times (once for every partition).


Crossref data
~~~~~~~~~~~~~

Crossref data concern works, identified through their DOI.

.. figure:: ./schema/crossref.svg
   :alt: Crossref data schema

ORCID data
~~~~~~~~~~

ORCID data concern work authors, identified through their ORCID.

.. figure:: ./schema/orcid.svg
   :alt: ORCID data schema

ROR data
~~~~~~~~

ROR data concern research organizations, identified through their DOI.

.. figure:: ./schema/ror.svg
   :alt: ROR data schema

Other data
~~~~~~~~~~

Other data include journal names, subjects (ASJCS), funders, and
open access journals, as well as join tables created through
available processing steps.

.. figure:: ./schema/other.svg
   :alt: Other data schema
