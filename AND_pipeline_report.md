# Author name disambiguation pipeline
This is a report on the author name disambiguation pipeline in alexandria3k. The pipeline aims to separate authors with the same name based on specific criteria in the populated Crossref dataset.

In this report I briefly describe the pipeline, optimizations, and some speed/correctness benchmarks so far.
## The pipeline so far

So far the author name disambiguation pipeline consists of 2 processes

- link_author_blocks.py

link_author_blocks reads the work_authors table as input.
Specifically, it reads "name" and "family" from each entry and passes them into a custom normalization function
Based on the normalized names/surnames, it splits all authors into "blocks" by surname and the first initial of the author's given name (e.g. john smith goes into block smith_j, similarly for james smith)
This is done to reduce the number of comparisons needed to distinguish between 2 authors.
In the end it produces an "author_name_blocks" table with fields (work_author_id, work_id, normalized_name, normalized_last_name, block_key) where block_key is the corresponding "smith_j" from the previous example, for each author.

For this process to work, the work_authors table must have been populated beforehand

The next process fully depends on the existence of the produced author_name_blocks table, so in the future they'll be merged into one process, but since they currently have fairly different functionality I've temporarily kept them as separate processes

- link_merged_authors.py

link_merged_authors.py takes as input the author_name_blocks described above.
For each block it compares all entries (i.e. the authors) with all others in the same block. This number is unavoidable, so the algorithm is necessarily quadratic in complexity, i.e. for a block of 10k entries, 50M comparisons are needed (n * (n-1) / 2).
Each comparison is made across several relevant metadata for each author in the dataset, and based on these a score is calculated - above a threshold, we consider them the same person.

The author attributes compared so far are:
- Name (Jaro-Winkler similarity)
- Affiliations (n-gram Jaccard)
- Co-authors (Jaccard on block keys)
- Publication year of the paper (year gap)
- Smaller comparison measures, such as: if two authors are co-authors, we immediately consider them different people.

These criteria mirror the signals used in S2AND, one of the more well-known author-name-disambiguation datasets
https://arxiv.org/pdf/2103.07534#table.3 .

The big difference is that S2AND uses a pre-trained classifier to determine whether a merge can be made, while in alexandria's pipeline, we compute it manually with some average and weights on specific signals.

The merging logic between two authors is done with a UnionFind (dis-joint set) datastructure.

https://en.wikipedia.org/wiki/Disjoint-set_data_structure

#### Depenedencies

- rapidfuzz for Jaro Winkler similarity
- scikit-learn for n-grams (likely for upcoming features too)

## Optimisations and Benchmarks

As mentioned above, the number of comparisons in a block is b^2, which for large blocks, due to the huge number of comparisons, dramatically increases execution time as shown in the table below for the 60MB sample dataset.

So I've implemented a few optimisations to reduce execution time:

- Grouping authors in the same block based on their hash across certain comparison metrics (all except work_id and title, which differ every time and don't affect the scores anyway). We treat people with the same hash as automatically the same person, so after grouping all authors with the same hash, we pick only one entry per group in the same block as the group's "representative" and only compare representatives of each group, drastically reducing the number of comparisons per block.

- Parallelization of the entire process using Python's standard library "multiprocessing". Since all blocks are independent of each other and don't affect one another, it's easy to parallelize the process. Specifically parallelization is implemented in two stages.  

    - Stage 1 of parallelization consists of processing bigger blocks (those with number of entries over a specific threshold, right now 50 entries). A fixed pool of worker processes is created once (one per CPU core), and each big block is dispatched to whichever worker is free, so blocks get processed in parallel without paying process-creation overhead per block. 

    - Stage 2 of parallelization consists of dividing the number of small blocks left into chunks and given to a number of processes, relative to the machines cpu cores. 

### Benchmarks, speed
| Dataset sample size | Number of entries | Blocking time (same regardless of optimisation) | Initial version without optimisations | Version with grouping hashed authors  | Parallelization + grouping hashes |
|---|---|---|---|---|---|
| 30MB   | 65,132    | 0.71s  | -       | 2.69s   | 1.76s   |
| 60MB   | 134,308   | 1.24s  | 109.85s | 7.11s   | 2.48s   |
| 120MB  | 271,421   | 2.94s  | -       | 32.65s  | 7.71s   |
| 150MB  | 382,953   | 3.94s  | -       | 43.49s  | 12.21s  |
| 200MB  | 510,358   | 6.05s  | -       | 82.14s  | 17.42s  |
| 300MB  | 726,402   | 7.37s  | -       | 185.47s | 36.11s  | 
| 450MB  | 1,039,231 | 10.75s | -       | 404.68s | 70.78s  |
| 700MB  | 1,555,447 | 21.18s | -       | 1019.41s| 213.60s |
| 1GB    | 2,034,695 | 22.89s | -       | -       | 271.2s  | 

### Benchmark, Correctness

To measure how correctly the pipeline works, we use Crossref's authenticated ORCID field: authors with the same real (verified) ORCID are considered certainly the same person. We compare this ground truth against the merging result by computing two percentages:

- **% correct merges**: of all the author pairs the pipeline merged, what percentage was actually correct.
- **% real pairs detected**: of all author pairs that are actually the same person (based on authenticated_orcid), what percentage did the pipeline manage to detect and merge.

| Dataset | % correct merges | % real pairs detected |
|---|---|---|
| 30MB   | 100% | 97% |
| 120MB  | 98%  | 79% |
| 700MB  | 97%  | 62% |

The % correct merges stays consistently high across all datasets (above 97%), meaning almost all merges we make are correct and there are no false positives. The % real pairs detected, however, drops significantly as the dataset grows (from 97% at 30MB to 62% at 700MB) - this is mainly due to two things:

1. The threshold (0.75) is deliberately strict to avoid false positives, at the cost of missing some real matches (false negatives).
2. Many of the missed pairs lack data such as affiliations (about 37% at the 700MB tier), which affects the likelihood of two authors being merged.

# Future plans / TODO list:

1. Make parallelism be supported for large distributed parallel systems using libraries like celery 
2. Filter dataset for a specific subset of the entire Crossref dataset (like Greek researchers) to test the pipeline there.
3. Train a logistic regression model that fine tunes the weights of specific signals for increased correctness