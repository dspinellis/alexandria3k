#!/usr/bin/env python3
#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2025  Panagiotis Spanakis
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Calculate context-normalized impact (generic; resembles SNIP) using Leiden clustering.

Context Normalized Impact measures citation impact by normalizing a journal's
raw citations-per-paper against the estimated citation potential of its field.
Fields are discovered through Leiden community detection on the bibliographic
coupling network.

This metric resembles the "Source Normalized Impact per Paper (SNIP)" metric in
that it normalizes citations-per-paper by an estimate of field citation potential.

Third-party metric names are referenced only for comparison. They may be
trademarks or registered trademarks of their respective owners.

Algorithm:
1. Build bibliographic coupling graph (journals sharing references)
2. Run Leiden clustering to discover research communities
3. Assign each journal to multiple communities (threshold derived from data via Otsu's method)
4. Calculate citation potential per community
5. Compute each journal's weighted citation potential
6. Score = Raw Impact per Paper / Citation Potential

Usage:
    ./context_normalized_impact.py
    ./context_normalized_impact.py --resolution 1.0

Environment Variables:
    MAINDB: Path to the main database (without .db extension). Default: 'impact'
    ROLAPDB: Path to the ROLAP database (without .db extension). Default: 'rolap'
"""

import argparse
from collections import Counter
import logging
import os
import sqlite3

import igraph as ig
import leidenalg
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


DEFAULT_RESOLUTION = 1.0
# Set to None for no hard cap on per-journal community assignments.
MAX_COMMUNITIES_PER_JOURNAL = None
MIN_COMMUNITY_SIZE = 3


def effective_limit(ranked_count: int) -> int:
    """Return the effective cap on community memberships per journal."""
    if MAX_COMMUNITIES_PER_JOURNAL is None:
        return ranked_count
    return min(MAX_COMMUNITIES_PER_JOURNAL, ranked_count)


def get_db_connection(db_path, rolap_db_path):
    """Establish connection to the main database and attach ROLAP."""
    if not os.path.exists(db_path):
        logging.critical(f"Main database file '{db_path}' not found.")
        raise FileNotFoundError(f"Database file '{db_path}' not found.")

    logging.info(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)

    if not os.path.exists(rolap_db_path):
        logging.critical(f"ROLAP database file '{rolap_db_path}' not found.")
        raise FileNotFoundError(f"Database file '{rolap_db_path}' not found.")

    logging.info(f"Attaching {rolap_db_path} as rolap...")
    conn.execute(f"ATTACH DATABASE '{rolap_db_path}' AS rolap")
    return conn


def load_bibliographic_coupling(conn):
    """Load the bibliographic coupling graph from the database."""
    logging.info("Loading bibliographic coupling data...")
    query = """
        SELECT journal_a, journal_b, coupling_strength
        FROM rolap.bibliographic_coupling
    """
    coupling_df = pd.read_sql_query(query, conn)
    logging.info(f"Loaded {len(coupling_df)} coupling edges.")
    return coupling_df


def load_journal_data(conn):
    """Load journal publication counts, citation counts, and reference density."""
    logging.info("Loading journal publication data (3-year window)...")

    publications_query = """
        SELECT journal_id, publications_number
        FROM rolap.publications3
    """
    publications_df = pd.read_sql_query(publications_query, conn)

    citations_query = """
        SELECT cited_journal AS journal_id, SUM(citation_count) AS citations
        FROM rolap.citation_network3
        GROUP BY cited_journal
    """
    citations_df = pd.read_sql_query(citations_query, conn)

    reference_query = """
        SELECT journal_id, avg_references
        FROM rolap.journal_reference_density
    """
    reference_df = pd.read_sql_query(reference_query, conn)

    logging.info(f"Loaded {len(publications_df)} journals with publications.")
    logging.info(f"Loaded {len(citations_df)} journals with citations.")
    logging.info(f"Loaded {len(reference_df)} journals with reference data.")

    return publications_df, citations_df, reference_df


def build_graph(coupling_df):
    """Build an igraph graph from the coupling DataFrame."""
    logging.info("Building bibliographic coupling graph...")

    journals = sorted(
        set(coupling_df["journal_a"]).union(set(coupling_df["journal_b"]))
    )
    journal_to_idx = {j: i for i, j in enumerate(journals)}

    edges = [
        (journal_to_idx[a], journal_to_idx[b])
        for a, b in zip(coupling_df["journal_a"], coupling_df["journal_b"])
    ]
    weights = coupling_df["coupling_strength"].tolist()

    g = ig.Graph(n=len(journals), edges=edges, directed=False)
    g.vs["journal_id"] = journals
    g.es["weight"] = weights

    logging.info(f"Graph has {g.vcount()} vertices and {g.ecount()} edges.")
    return g, journals, journal_to_idx


def run_leiden_clustering(g, resolution=DEFAULT_RESOLUTION):
    """Run Leiden clustering and return the partition."""
    logging.info(f"Running Leiden clustering (resolution={resolution})...")

    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=resolution,
        n_iterations=-1,
        seed=42,
    )

    n_communities = len(partition)
    logging.info(f"Found {n_communities} communities.")

    sizes = [len(c) for c in partition]
    if sizes:
        logging.info(
            f"Community sizes: min={min(sizes)}, max={max(sizes)}, median={np.median(sizes):.0f}"
        )

    return partition


def _otsu_threshold(values: np.ndarray) -> float:
    """Find the threshold that minimizes within-class variance (Otsu's method).

    Applied to the distribution of secondary/primary strength ratios to
    automatically determine which multi-community assignments are meaningful.
    """
    if len(values) < 2:
        return 0.5
    n_bins = min(256, len(values))
    hist, bin_edges = np.histogram(values, bins=n_bins, range=(0.0, 1.0))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    hist = hist.astype(float)
    total = hist.sum()
    if total == 0:
        return 0.5
    hist /= total
    w1 = np.cumsum(hist)
    w2 = 1.0 - w1
    mu1 = np.cumsum(hist * bin_centers) / np.where(w1 > 0, w1, 1.0)
    mu2 = (np.sum(hist * bin_centers) - np.cumsum(hist * bin_centers)) / np.where(
        w2 > 0, w2, 1.0
    )
    inter_var = w1 * w2 * (mu1 - mu2) ** 2
    return float(bin_centers[np.argmax(inter_var)])


def _merge_small_communities(g, partition):
    """Reassign journals in communities smaller than MIN_COMMUNITY_SIZE.

    Each journal in a too-small community is moved to its nearest large
    neighbor community, determined by the strongest coupling weight.
    Returns the (possibly modified) membership list.
    """
    membership = list(partition.membership)
    community_sizes = Counter(membership)

    large_communities = {
        cid for cid, size in community_sizes.items() if size >= MIN_COMMUNITY_SIZE
    }

    if len(large_communities) == len(community_sizes):
        logging.info("No small communities to merge.")
        return membership

    for vertex_idx in range(g.vcount()):
        if membership[vertex_idx] in large_communities:
            continue

        neighbors = g.neighbors(vertex_idx)
        best_community = None
        best_weight = -1.0
        for n in neighbors:
            n_community = membership[n]
            if n_community not in large_communities:
                continue
            weight = g.es[g.get_eid(vertex_idx, n)]["weight"]
            if weight > best_weight:
                best_weight = weight
                best_community = n_community

        if best_community is not None:
            membership[vertex_idx] = best_community

    n_reassigned = sum(
        1 for old, new in zip(partition.membership, membership) if old != new
    )
    logging.info(f"Merged small communities: reassigned {n_reassigned} journals.")
    return membership


def assign_journals_to_communities(
    g,
    partition,
    journals,
    threshold_override=None,
):
    """Assign each journal to multiple communities based on coupling similarity.

    The secondary-assignment threshold is derived automatically from the data
    using Otsu's method on the distribution of secondary/primary strength ratios,
    unless overridden by ``threshold_override``.

    Community ids are stored as 1-based integers for readability.
    """
    logging.info("Assigning journals to communities (multi-assignment)...")

    membership = _merge_small_communities(g, partition)

    # Pass 1: compute per-journal ranked community strengths.
    strengths_by_journal = {}
    for vertex_idx, journal_id in enumerate(journals):
        neighbors = g.neighbors(vertex_idx)
        neighbor_weights = [g.es[g.get_eid(vertex_idx, n)]["weight"] for n in neighbors]

        community_strengths = {}
        for neighbor_idx, weight in zip(neighbors, neighbor_weights):
            community_id = int(membership[neighbor_idx]) + 1
            community_strengths[community_id] = (
                community_strengths.get(community_id, 0) + weight
            )

        if not community_strengths:
            own_community = int(membership[vertex_idx]) + 1
            community_strengths = {own_community: 1.0}

        strengths_by_journal[journal_id] = sorted(
            community_strengths.items(),
            key=lambda item: (-item[1], item[0]),
        )

    # Derive threshold from data via Otsu's method on secondary/primary ratios.
    if threshold_override is not None:
        threshold_min = threshold_override
        logging.info(
            f"Using explicit secondary assignment threshold: {threshold_min:.3f}"
        )
    else:
        ratios = []
        for ranked in strengths_by_journal.values():
            limit = effective_limit(len(ranked))
            if limit >= 2:
                primary_strength = ranked[0][1]
                for i in range(1, limit):
                    ratios.append(ranked[i][1] / primary_strength)
        threshold_min = _otsu_threshold(np.array(ratios)) if ratios else 0.5
        logging.info(
            f"Adaptive secondary assignment threshold (Otsu): {threshold_min:.3f} "
            f"(computed from {len(ratios)} candidate secondary assignments)"
        )

    # Pass 2: apply threshold.
    journal_community_strength = []
    for journal_id, ranked in strengths_by_journal.items():
        primary_strength = ranked[0][1]
        threshold = primary_strength * threshold_min
        limit = effective_limit(len(ranked))
        for index, (community_id, strength) in enumerate(ranked):
            if index >= limit:
                break
            if index == 0 or strength >= threshold:
                journal_community_strength.append(
                    {
                        "journal_id": journal_id,
                        "community_id": community_id,
                        "strength": strength,
                    }
                )

    assignments_df = pd.DataFrame(journal_community_strength)

    total_per_journal = assignments_df.groupby("journal_id")["strength"].transform(
        "sum"
    )
    assignments_df["weight"] = assignments_df["strength"] / total_per_journal

    n_multi = (assignments_df.groupby("journal_id").size() > 1).sum()
    logging.info(
        f"Assigned journals to communities: {len(assignments_df)} total assignments."
    )
    logging.info(f"Journals with multiple community assignments: {n_multi}")
    logging.info(
        f"Average communities per journal: {assignments_df.groupby('journal_id').size().mean():.2f}"
    )

    # Runtime invariant: primary weight must be >= 0.5 for every journal.
    primary_weights = (
        assignments_df.sort_values("weight", ascending=False)
        .groupby("journal_id")["weight"]
        .first()
    )
    n_violating = (primary_weights < 0.5).sum()
    logging.info(
        f"Journals with primary weight < 0.5: {n_violating} / {len(primary_weights)} (expected 0)"
    )

    return assignments_df[["journal_id", "community_id", "weight"]]


def calculate_citation_potential(assignments_df, reference_df):
    """Calculate citation potential for each community (weighted average reference density)."""
    logging.info("Calculating citation potential per community...")

    merged = assignments_df.merge(reference_df, on="journal_id", how="left")

    median_refs = reference_df["avg_references"].median()
    merged["avg_references"] = merged["avg_references"].fillna(median_refs)

    merged["weighted_refs"] = merged["avg_references"] * merged["weight"]
    community_potential = (
        merged.groupby("community_id")
        .agg({"weighted_refs": "sum", "weight": "sum"})
        .reset_index()
    )

    community_potential["citation_potential"] = (
        community_potential["weighted_refs"] / community_potential["weight"]
    )
    logging.info(
        f"Calculated citation potential for {len(community_potential)} communities."
    )

    return community_potential[["community_id", "citation_potential"]]


def calculate_journal_citation_potential(assignments_df, community_potential_df):
    """Calculate weighted citation potential for each journal."""
    logging.info("Calculating journal-level citation potential...")

    merged = assignments_df.merge(community_potential_df, on="community_id", how="left")
    merged["weighted_potential"] = merged["citation_potential"] * merged["weight"]
    journal_potential = (
        merged.groupby("journal_id")["weighted_potential"].sum().reset_index()
    )
    journal_potential.columns = ["journal_id", "citation_potential"]

    logging.info(
        f"Calculated citation potential for {len(journal_potential)} journals."
    )
    return journal_potential


def calculate_context_impact(publications_df, citations_df, journal_potential_df):
    """Calculate Context Normalized Impact for each journal.

    impact_score = raw_impact / citation_potential
    raw_impact = citations / publications_number
    """
    logging.info("Calculating context-normalized impact scores...")

    result = publications_df.merge(citations_df, on="journal_id", how="left")
    result = result.merge(journal_potential_df, on="journal_id", how="left")

    result["citations"] = result["citations"].fillna(0)

    result["raw_impact"] = result["citations"] / result["publications_number"]
    result["raw_impact"] = result["raw_impact"].replace([np.inf, -np.inf], 0)

    result["impact_score"] = result["raw_impact"] / result["citation_potential"]
    result["impact_score"] = result["impact_score"].replace([np.inf, -np.inf], 0)
    result["impact_score"] = result["impact_score"].fillna(0)

    result["impact_score"] = result["impact_score"].round(3)
    result["raw_impact"] = result["raw_impact"].round(3)
    result["citation_potential"] = result["citation_potential"].round(3)

    logging.info(f"Calculated scores for {len(result)} journals.")
    logging.info(
        f"Score statistics: min={result['impact_score'].min():.3f}, "
        f"max={result['impact_score'].max():.3f}, "
        f"median={result['impact_score'].median():.3f}"
    )

    return result[["journal_id", "impact_score", "raw_impact", "citation_potential"]]


def calculate_context_impact_fallback(publications_df, citations_df, reference_df):
    """Fallback calculation when Leiden clustering is unavailable."""
    logging.warning("Using fallback calculation (no community detection).")

    result = publications_df.merge(citations_df, on="journal_id", how="left")
    result = result.merge(reference_df, on="journal_id", how="left")

    result["citations"] = result["citations"].fillna(0)
    median_refs = reference_df["avg_references"].median()
    result["avg_references"] = result["avg_references"].fillna(median_refs)

    result["citation_potential"] = result["avg_references"]

    result["raw_impact"] = result["citations"] / result["publications_number"]
    result["raw_impact"] = result["raw_impact"].replace([np.inf, -np.inf], 0)

    result["impact_score"] = result["raw_impact"] / result["citation_potential"]
    result["impact_score"] = result["impact_score"].replace([np.inf, -np.inf], 0)
    result["impact_score"] = result["impact_score"].fillna(0)

    result["impact_score"] = result["impact_score"].round(3)
    result["raw_impact"] = result["raw_impact"].round(3)
    result["citation_potential"] = result["citation_potential"].round(3)

    logging.info(f"Calculated fallback scores for {len(result)} journals.")
    return result[["journal_id", "impact_score", "raw_impact", "citation_potential"]]


def write_df_to_attached(
    conn: sqlite3.Connection, df: pd.DataFrame, table: str, db: str = "rolap"
):
    """
    Drop and recreate table `db.table` and load DataFrame contents.
    Works with sqlite3 and attached databases.
    """
    cols = list(df.columns)

    # simple type mapping
    type_map = {
        "int64": "INTEGER",
        "float64": "REAL",
        "bool": "INTEGER",
        "object": "TEXT",
    }
    col_defs = []
    for c in cols:
        sql_type = type_map.get(str(df[c].dtype), "TEXT")
        col_defs.append(f'"{c}" {sql_type}')

    conn.execute(f'DROP TABLE IF EXISTS {db}."{table}"')
    conn.execute(f'CREATE TABLE {db}."{table}" ({", ".join(col_defs)})')

    quoted_cols = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f'INSERT INTO {db}."{table}" ({quoted_cols}) VALUES ({placeholders})'

    conn.executemany(insert_sql, df.itertuples(index=False, name=None))
    conn.commit()


def save_results(conn, impact_df, assignments_df=None, community_potential_df=None):
    """Save results and intermediate data to the database."""
    logging.info("Saving results to database...")

    write_df_to_attached(conn, impact_df, "context_impact")
    logging.info(f"Saved {len(impact_df)} scores to rolap.context_impact")

    if assignments_df is not None:
        write_df_to_attached(conn, assignments_df, "journal_communities")
        logging.info(
            f"Saved {len(assignments_df)} community assignments to rolap.journal_communities"
        )

    if community_potential_df is not None:
        conn.execute("DROP TABLE IF EXISTS rolap.community_citation_potential")
        write_df_to_attached(
            conn, community_potential_df, "community_citation_potential"
        )
        logging.info(
            f"Saved {len(community_potential_df)} community potentials to rolap.community_citation_potential"
        )

    conn.commit()


def main():
    parser = argparse.ArgumentParser(
        description="Calculate context-normalized impact (generic; resembles SNIP) using Leiden community detection."
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=DEFAULT_RESOLUTION,
        help="Leiden resolution parameter",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Secondary assignment threshold (default: adaptive via Otsu's method)",
    )
    parser.add_argument("--db", help="Path to the main SQLite database")
    parser.add_argument("--rolap-db", help="Path to the ROLAP SQLite database")
    parser.add_argument(
        "--test-db",
        help="Single database file used for both main and ROLAP (for testing)",
    )
    args = parser.parse_args()

    if args.test_db:
        db_path = args.test_db
        rolap_db_path = args.test_db
    elif args.db and args.rolap_db:
        db_path = args.db
        rolap_db_path = args.rolap_db
    else:
        parser.error("Provide either --test-db or both --db and --rolap-db")

    try:
        conn = get_db_connection(db_path, rolap_db_path)

        publications_df, citations_df, reference_df = load_journal_data(conn)
        coupling_df = load_bibliographic_coupling(conn)

        if len(coupling_df) == 0:
            logging.warning("No bibliographic coupling data. Using fallback.")
            impact_df = calculate_context_impact_fallback(
                publications_df, citations_df, reference_df
            )
            save_results(conn, impact_df)
        else:
            g, journals, _ = build_graph(coupling_df)
            partition = run_leiden_clustering(g, resolution=args.resolution)

            assignments_df = assign_journals_to_communities(
                g,
                partition,
                journals,
                threshold_override=args.threshold,
            )

            community_potential_df = calculate_citation_potential(
                assignments_df, reference_df
            )
            journal_potential_df = calculate_journal_citation_potential(
                assignments_df, community_potential_df
            )

            impact_df = calculate_context_impact(
                publications_df, citations_df, journal_potential_df
            )
            save_results(conn, impact_df, assignments_df, community_potential_df)

        logging.info("Context-normalized impact calculation complete.")

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
