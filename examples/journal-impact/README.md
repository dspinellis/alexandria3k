# Calculate journal impact metrics

This directory contains the implementation for calculating diverse journal impact metrics, including:

Third-party metric names are referenced only for comparison. They may be trademarks or registered trademarks of their respective owners.

* **Two-Year Citation Mean**
    * *Description:* Calculates the mean number of citations received per paper published in the preceding two years.
   * *Note:* This metric resembles the [Journal Impact Factor](https://en.wikipedia.org/wiki/Impact_factor).

* **Journal Network Centrality**
    * *Description:* Measures the journal's total importance within the citation network using a PageRank-style algorithm.
   * *Note:* This metric resembles the [Eigenfactor score](http://www.eigenfactor.org/methods.pdf).

* **Prestige Weighted Rank**
    * *Description:* A size-independent metric that weights citations based on the prestige of the citing journal.
    * *Note:* This metric is similar to the [SCImago Journal Rank (SJR)](https://en.wikipedia.org/wiki/SCImago_Journal_Rank).

* **Mean Article Network Score**
    * *Description:* Calculates the average influence per article by normalizing the network centrality score against the journal's publication volume.
   * *Note:* This metric resembles the [Article Influence Score](https://en.wikipedia.org/wiki/Eigenfactor#Article_Influence_Score).

* **Context Normalized Impact**
    * *Description:* Measures contextual citation impact by weighting citations based on the total number of citations in a subject field.
   * *Note:* This metric resembles the [Source Normalized Impact per Paper (SNIP)](https://www.sciencedirect.com/science/article/abs/pii/S1751157712001010?via%3Dihub).

A journal's Two-Year Citation Mean is based on the ratio between its publications
and references to them.
The other metrics use eigenvector centrality to measure journal importance,
with different normalization approaches to account for field differences
and journal size.

## Journal Network Centrality (resembles Eigenfactor) calculation overview

The Journal Network Centrality score measures a journal's total importance to the
scientific community, calculated similarly to Google's PageRank algorithm. 

The calculation involves the following steps:
1. **Data Preparation**: Aggregating citation data (5-year window)
   and article counts from the main database into indexed intermediate tables.
2. **Self-Citation Removal**: Journal self-citations are completely excluded
   from the citation network.
3. **Score Calculation**: The Python script (`journal_network_metrics.py`)
   reads the aggregated data,
   constructs a sparse adjacency matrix of the citation network, and
   computes the principal eigenvector using the power iteration method.
4. **Normalization**: Scores are normalized so that all journals sum to 100%.
5. **Reporting**: The calculated scores are stored in the database
   for subsequent reporting.

## Prestige Weighted Rank (resembles SJR) calculation overview

The Prestige Weighted Rank measures prestige per article, accounting for both
the number and quality of citations received.

Key differences from Journal Network Centrality:
1. **3-year citation window**: Uses a shorter time frame than the network centrality calculation.
2. **Limited self-citations**: Self-citations are capped at 33% of incoming
   citations (not excluded entirely), reflecting that some self-citation
   is normal academic practice.
3. **Per-article normalization**: Scores are normalized by article count,
   then scaled so the average journal has a score = 1.0.
   This makes the metric size-independent.

Run with: `./journal_network_metrics.py --metric prestige_rank`

## Mean Article Network Score (resembles AIS) calculation overview

The Mean Article Network Score measures the average influence of a journal's articles over 5 years.
It is essentially the Journal Network Centrality score normalized by the journal's
article output, making it comparable to the traditional Two-Year Citation Mean.

Key characteristics:
1. **5-year citation window**: Same as Journal Network Centrality.
2. **Excluded self-citations**: Same as Journal Network Centrality.
3. **Per-article normalization**: Divides prestige by article count,
   then scales so the average article has a score = 1.0.
   A score > 1.0 means above-average influence per article.

Run with: `./journal_network_metrics.py --metric mean_article_score`

## Context Normalized Impact (resembles SNIP) calculation overview

Context Normalized Impact measures contextual citation impact by normalizing citations
against the citation potential of each journal's field.
This makes the metric directly comparable across different disciplines.

The calculation uses Leiden community detection on the bibliographic
coupling network to discover research fields organically:

1. **Bibliographic Coupling Network**: A weighted graph is constructed where
   journals are nodes and edges represent shared references. Two journals
   are connected if they cite common sources; the edge weight is the
   number of shared references. 
2. **Leiden Clustering**: The Leiden algorithm (an improved version of Louvain)
   is applied to discover communities of related journals. Unlike seeded
   approaches, this finds fields based on actual citation patterns without
   bias toward high-citation areas.
3. **Multi-Community Assignment**: Journals can belong to multiple communities.
   A journal is assigned to a community if its coupling strength to that
   community is ≥30% of its maximum coupling strength. This handles
   interdisciplinary journals naturally.
4. **Citation Potential per Community**: For each community, the weighted
   average reference density is calculated based on member journals.
5. **Journal Citation Potential**: Each journal's citation potential is the
   weighted average of its communities' potentials.
6. **Score Calculation**: Score = (Citations/Paper) / Citation_Potential

Key advantages of the Leiden approach:
- **No bias toward high-citation fields**: Communities emerge from data
- **Handles niche fields**: Even low-citation areas form communities
- **Better interdisciplinary handling**: Multi-community assignment
- **Reproducible**: Uses a fixed random seed for deterministic results

This metric is calculated using the `context_normalized_impact.py` Python script, which requires
the `leidenalg` and `python-igraph` packages. Run with: `make tables/context_impact`

## Dependencies

The Journal Network Centrality, Prestige Weighted Rank, and Mean Article Network Score calculations require the installation of
the _pandas_, _numpy_, and _scipy_ Python packages.

The Context Normalized Impact calculation additionally requires the _leidenalg_ and _python-igraph_
packages for community detection.

Install them with your favourite Python package manager (e.g. _uv_, _pip_),
ideally in a virtual environment.

## Journal Impact Report Fields

The file `reports/journal-impact-report.txt` contains the following columns for each journal:

- **title**: Journal title
- **publisher**: Journal publisher
- **issn_print**: Print ISSN
- **issn_eprint**: Electronic ISSN
- **issns_additional**: Additional ISSNs (if any)
- **doi**: Journal DOI (if available)
- **citations_number2**: Number of citations received in the 2-year window (for Two-Year Citation Mean)
- **publications_number2**: Number of articles published in the 2-year window
- **citation_mean_2y**: Two-Year Citation Mean (citations_number2 / publications_number2). *Resembles the Journal Impact Factor.*
- **citations_number5**: Number of citations received in the 5-year window
- **publications_number5**: Number of articles published in the 5-year window
- **citation_mean_5y**: Five-Year Citation Mean (citations_number5 / publications_number5). *Similar to 5-Year Impact Factor.*
- **h5_index**: h5-index (number of articles with at least h citations in the last 5 years)
- **h5_median**: Median number of citations for articles in the h5-index
- **network_centrality**: Journal Network Centrality (journal's overall influence in the citation network). *Resembles the Eigenfactor score.*
- **prestige_rank**: Prestige Weighted Rank (prestige per article, normalized). *Resembles the SCImago Journal Rank (SJR) metric.*
- **mean_article_score**: Mean Article Network Score (average influence per article). *Resembles the Article Influence Score (AIS) metric.*
- **context_impact**: Context Normalized Impact (normalized by field citation potential). *Resembles the Source Normalized Impact per Paper (SNIP) metric.*
- **clusters**: Journal Communities (hyphen-separated list of community IDs the journal belongs to, e.g., 1-2)

This report provides a comprehensive comparison of journals across multiple impact metrics and citation windows.
