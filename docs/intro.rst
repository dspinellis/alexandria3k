.. Auto-generated file; run bin/update-intro to update it.

The *alexandria3k* Python package supplies a command-line tool and an
API providing fast and space-efficient relational query access to the
following large scientific publication open data sets. Data are
decompressed on the fly, thus allowing the package’s use even on
storage-restricted laptops. The *alexandria3k* package supports the
following large data sets.

-  `Crossref <https://www.nature.com/articles/d41586-022-02926-y>`__
   (184 GiB compressed, 1.9 TiB uncompressed — as of March 2025). This
   contains publication metadata from all major international
   publishers. The Crossref data set is split into about 33 thousand
   files. Each file contains JSON data for 5000 publications (works). In
   total, Crossref contains data for 167 million works, 35 million
   abstracts, 465 million associated work authors, and 2.5 billion
   references.

-  `PubMed <https://pubmed.ncbi.nlm.nih.gov/>`__ (47 GiB compressed, 707
   GiB uncompressed — as of April 2025). This comprises more than 36
   million citations for biomedical literature from
   `MEDLINE <https://www.nlm.nih.gov/medline/medline_overview.html>`__,
   life science journals, and online books, with rich domain-specific
   metadata, such as
   `MeSH <https://www.nlm.nih.gov/mesh/meshhome.html>`__ indexing,
   funding, genetic, and chemical details.

-  `ORCID summary data
   set <https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file->`__
   (37 GiB compressed, 651 GiB uncompressed — as of October 2024). This
   contains about 22 million author details records.

-  `DataCite <https://datacite.org/>`__ (24 GiB compressed, 347 GiB
   uncompressed — as of 2024). This comprises research outputs and
   resources, such as data, pre-prints, images, and samples, containing
   about 50 million work entries.

-  `United States Patent Office issued
   patents <https://bulkdata.uspto.gov/>`__ (12 GiB compressed, 128 GiB
   uncompressed — as of January 2025). This contains about 5.4 million
   records.

Further supported data sets include funder bodies, journal names, open
access journals, and research organizations.

The *alexandria3k* package installation contains all elements required
to run it. It does not require the installation, configuration, and
maintenance of a third party relational or graph database. It can
therefore be used out-of-the-box for performing reproducible publication
research on the desktop.

Databases populated with *alexandria3k* can be used by generative AI
applications through the `Model Context
Protocol <https://modelcontextprotocol.io/>`__ and its
`SQLite <https://github.com/modelcontextprotocol/servers/blob/main/src/sqlite>`__
reference server. Application examples include topic modeling,
snowballing, trend analysis, author disambiguation, citation graph
generation, research trend analysis, patent similarity detection, grant
and funding prediction, co-authorship network mapping, institutional
collaboration analysis, knowledge graph augmentation, research impact
prediction, academic fraud detection, technology transfer mapping,
interdisciplinary research discovery, and research paper
recommendations.
