Data downloading
----------------

To use *alexandria3k* you need to download the open data you require
for your study.

Crossref data
~~~~~~~~~~~~~

The main data set on which *alexandria3k* operates is that of
`Crossref <https://www.crossref.org>`__, comprising about 130 million
publication metadata records with more than 1.7 billion reference
records and 359 million author records. You can obtain the data from
`Acedemic
Torrents <https://academictorrents.com/browse.php?search=crossref>`__
using a torrent client of your choice. Below is an example of commands
that download the April 2022 Crossref snapshot (the one on which
*alexandria3k* has been tested) using the
`aria2c <https://aria2.github.io/>`__ download utility.

.. code:: sh

   # Download Crossref data (168 GB) through the torrent link
   aria2c https://doi.org/10.13003/83b2gq

Currently, the Crossref data set is split into about 26 thousand
compressed files, each containing JSON data for 3000 publications
(works). *Alexandria3k* provides a relational view of these data, and
also allows the sampling of a subset of the container files to quickly
experiment with queries, before they are run on the complete set.

DataCite data
~~~~~~~~~~~~~
You can download the DataCite Public Data File after a simple registration
from the
`DataCite Data Files Service <https://datafiles.datacite.org/>`__.

ORCID data
~~~~~~~~~~

You can populate a database with data regarding authors (URLs,
countries, external identifiers, education, employment, works, etc.)
from the `ORCID <https://orcid.org/>`__ initiative. For this you need to
download the *summary file* of the ORCID Public Data File
(e.g. ``ORCID_2022_10_summaries.tar.gz`` — 25GB) through
`Figshare <https://orcid.figshare.com/>`__. Note that *alexandria3k*
works on the compressed file; there is no need to expand it (it expands
to about 0.5 TB).

PubMed data
~~~~~~~~~~~

You can populate a database with the data from the PubMed/MEDLINE database
from the National Library of Medicine (NLM).
The data are available from
`here <https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/>`__.
You can also download the data from the FTP server which is documented in
`this readme file <https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/README.txt>`__.
Publication data are overlapping with the Crossref dataset,
but the PubMed data contain additional information
such as MeSH terms and grants.
They also complement the Crossref data as for example some affiliations
are only available in the PubMed data.

The shell script ``examples/common/fetch-pubmed.sh`` or the
``$(PUBMED_DIR)`` dependency of the ``examples/common/Makefile``,
which uses it, can be used to download all PubMed data.

USPTO data
~~~~~~~~~~

You can populate a database with the bibliographic text (front page) of each
patent application published weekly from 2003 to present. These data are published
from the US Patent and Trademark Office (USPTO) and hence the data source acronym used in *alexandria3k*.
Some of the key components of bibliographic data in a USPTO patent are
title,
inventors,
assignee,
publication date,
references,
citations,
related documents, etc.

Follow these steps to explore the USPTO patent bibliographic data with the magic of *alexandria3k*.

**Downloading Data**:
To access the required data, download it from the USPTO's bulk data page `here <https://bulkdata.uspto.gov/>`__.

**Select the Correct Dataset**:
There are various datasets available; ensure you select the "Patent Grant Bibliographic (Front Page) Text Data (JAN 1976 - PRESENT)" dataset. From there on you can choose weekly issued patent files from year 2005 to now.

**Organizing Downloaded Data**:
Organize the downloaded data by ensuring that each zip file is placed under a folder representing the year it was published. This step is crucial for operating properly.


.. code-block:: text

   /data
   ├── 2023
   │   ├── ipgb20230131_wk05.zip
   │   └── ipgb20230207_wk06.zip
   ├── 2010
       ├── ipgb20100223_wk08.zip
       └── ipgb20100302_wk09.zip

The shell script ``examples/common/fetch-uspto.sh`` or the
``$(USPTO_DIR)`` dependency of the ``examples/common/Makefile``,
which uses it, can be used to download all USPTO data.


Other data sources
~~~~~~~~~~~~~~~~~~

The *alexandria3k* system can also add to a database the following
tables. You can download the data and point *alexandria3k* to the
corresponding file, or, because the data sets are relatively small, you
can provide *alexandria3k* the URL from which it will directly stream
the data to populate the database.

-  `Crossref journal
   data <http://ftp.crossref.org/titlelist/titleFile.csv>`__ (109k
   records)
-  `Crossref funder
   data <https://doi.crossref.org/funderNames?mode=list>`__ (21k
   records)
-  `Open access journal metadata <https://doaj.org/csv>`__ from the
   `directory of open access journals <https://doaj.org/>`__ (19k
   records)
-  `Research organization
   data <https://doi.org/10.5281/zenodo.7448410>`__ from the `Research
   Organization Registry — ROR <https://ror.org/>`__ (595k records)
