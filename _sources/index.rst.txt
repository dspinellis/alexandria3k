Alexandria3k documentation
==========================

The *alexandria3k* package supplies a library and a command-line tool
providing efficient relational query access to the following large
scientific publication open data sets. Data are decompressed on the fly,
thus allowing the package’s use even on storage-restricted laptops.

-  `Crossref <https://www.nature.com/articles/d41586-022-02926-y>`__
   (157 GB compressed, 1 TB uncompressed). This contains publication
   metadata from about 134 million publications from all major
   international publishers with full citation data for 60 million of
   them.
-  `PubMed <https://pubmed.ncbi.nlm.nih.gov/>`__ (43 GB compressed, 327
   GB uncompressed). This comprises more than 36 million citations for
   biomedical literature from
   `MEDLINE <https://www.nlm.nih.gov/medline/medline_overview.html>`__,
   life science journals, and online books, with rich domain-specific
   metadata, such as
   `MeSH <https://www.nlm.nih.gov/mesh/meshhome.html>`__ indexing,
   funding, genetic, and chemical details.
-  `ORCID summary data
   set <https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file->`__
   (25 GB compressed, 435 GB uncompressed). This contains about 78
   million author details records.
-  `DataCite <https://datacite.org/>`__ (22 GB compressed, 197 GB
   uncompressed). This comprises research outputs and resources, such as
   data, pre-prints, images, and samples, containing about 50 million
   work entries.
-  `United States Patent Office issued
   patents <https://bulkdata.uspto.gov/>`__ (11 GB compressed, 115 GB
   uncompressed). This containins about 5.4 million records.

Further supported data sets include funder bodies, journal names, open
access journals, and research organizations.

The *alexandria3k*
package installation contains all elements required to run it. It does
not require the installation, configuration, and maintenance of a third
party relational or graph database. It can therefore be used
out-of-the-box for performing reproducible publication research on the
desktop.

Publication
-----------

Details about the rationale, design, implementation, and use of this
software can be found in the following paper.

Diomidis Spinellis. Open reproducible scientometric research with Alexandria3k. *PLoS ONE* 18(11): e0294946. November 2023. `doi: 10.1371/journal.pone.0294946 <https://doi.org/10.1371/journal.pone.0294946>`__

Package name derivation
-----------------------

The *alexandria3k* package is named after the `Library of
Alexandria <https://en.wikipedia.org/wiki/Library_of_Alexandria>`__,
indicating how publication data can be processed in the third millenium
AD.

Contents
========

.. toctree::
   :maxdepth: 2

   installation
   downloading
   use
   cli-eg
   python-eg
   app-eg
   schema
   cli
   user-api
   plugin-api
   utility-api
   dev
   dev-plugin
   faq


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

