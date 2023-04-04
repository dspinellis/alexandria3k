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
