Alexandria3k documentation
==========================

The *alexandria3k* package supplies a library and a command-line tool
providing efficient relational query access to diverse publication open
data sets.
The largest one is the entire `Crossref data
set <https://www.nature.com/articles/d41586-022-02926-y>`__ (157 GB
compressed, 1 TB uncompressed). This contains publication metadata from
about 134 million publications from all major international publishers
with full citation data for 60 million of them.
In addition, the Crossref data set can be linked with the `ORCID summary
data
set <https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file->`__
(25 GB compressed, 435 GB uuncompressed), containing about 78 million
author records,
the `US Patent and Trademark Office issued patents <https://bulkdata.uspto.gov>`__ 
(11 GB compressed, 115 GB uncompressed), containing about 5.4 million records,
as well as data sets of funder bodies, journal names,
open access journals, and research organizations.
from 2005 to present (11 GB compressed).

The *alexandria3k*
package installation contains all elements required to run it. It does
not require the installation, configuration, and maintenance of a third
party relational or graph database. It can therefore be used
out-of-the-box for performing reproducible publication research on the
desktop.

Pre-print and citation
----------------------

Details about the rationale, design, implementation, and use of this
software can be found in the following paper.

Diomidis Spinellis. Open Reproducible Systematic Publication Research.
arXiv:2301.13312, January 2023.
`doi 10.48550/arXiv.2301.13312 <https://doi.org/10.48550/arXiv.2301.13312>`__

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

