#!/usr/bin/env python
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
3. Assign each journal to multiple communities (within 30% of max similarity)
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
import os
import sqlite3
import logging

import pandas as pd
import numpy as np

import igraph as ig
import leidenalg


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


DEFAULT_RESOLUTION = 1.0
SIMILARITY_THRESHOLD_MIN = 0.30  # Minimum 30% of max similarity for multi-assignment
SIMILARITY_THRESHOLD_MAX = 0.40  # Maximum 40% of max similarity
MIN_COMMUNITY_SIZE = 3


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

    journals = sorted(set(coupling_df["journal_a"]).union(set(coupling_df["journal_b"])))
    journal_to_idx = {j: i for i, j in enumerate(journals)}

    edges = [(journal_to_idx[a], journal_to_idx[b]) for a, b in zip(coupling_df["journal_a"], coupling_df["journal_b"])]
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


def assign_journals_to_communities(
    g,
    partition,
    journals,
    threshold_min=SIMILARITY_THRESHOLD_MIN,
    threshold_max=SIMILARITY_THRESHOLD_MAX,
):
    """Assign each journal to multiple communities based on coupling similarity.

    Community ids are stored as 1-based integers for readability.
    """
    logging.info("Assigning journals to communities (multi-assignment)...")

    journal_community_strength = []

    for vertex_idx, journal_id in enumerate(journals):
        neighbors = g.neighbors(vertex_idx)
        neighbor_weights = [g.es[g.get_eid(vertex_idx, n)]["weight"] for n in neighbors]

        community_strengths = {}
        for neighbor_idx, weight in zip(neighbors, neighbor_weights):
            community_id = int(partition.membership[neighbor_idx]) + 1
            community_strengths[community_id] = community_strengths.get(community_id, 0) + weight

        if not community_strengths:
            own_community = int(partition.membership[vertex_idx]) + 1
            journal_community_strength.append(
                {"journal_id": journal_id, "community_id": own_community, "strength": 1.0}
            )
            continue

        max_strength = max(community_strengths.values())
        threshold = max_strength * threshold_min

        for community_id, strength in community_strengths.items():
            if strength >= threshold:
                journal_community_strength.append(
                    {"journal_id": journal_id, "community_id": community_id, "strength": strength}
                )

    assignments_df = pd.DataFrame(journal_community_strength)

    total_per_journal = assignments_df.groupby("journal_id")["strength"].transform("sum")
    assignments_df["weight"] = assignments_df["strength"] / total_per_journal

    n_multi = (assignments_df.groupby("journal_id").size() > 1).sum()
    logging.info(f"Assigned journals to communities: {len(assignments_df)} total assignments.")
    logging.info(f"Journals with multiple community assignments: {n_multi}")

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

    community_potential["citation_potential"] = community_potential["weighted_refs"] / community_potential["weight"]
    logging.info(f"Calculated citation potential for {len(community_potential)} communities.")

    return community_potential[["community_id", "citation_potential"]]


def calculate_journal_citation_potential(assignments_df, community_potential_df):
    """Calculate weighted citation potential for each journal."""
    logging.info("Calculating journal-level citation potential...")

    merged = assignments_df.merge(community_potential_df, on="community_id", how="left")
    merged["weighted_potential"] = merged["citation_potential"] * merged["weight"]
    journal_potential = merged.groupby("journal_id")["weighted_potential"].sum().reset_index()
    journal_potential.columns = ["journal_id", "citation_potential"]

    logging.info(f"Calculated citation potential for {len(journal_potential)} journals.")
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


def save_results(conn, impact_df, assignments_df=None, community_potential_df=None):
    """Save results and intermediate data to the database."""
    logging.info("Saving results to database...")

    conn.execute("DROP TABLE IF EXISTS rolap.context_impact")
    impact_df.to_sql("context_impact", conn, schema="rolap", index=False, if_exists="replace")
    logging.info(f"Saved {len(impact_df)} scores to rolap.context_impact")

    if assignments_df is not None:
        conn.execute("DROP TABLE IF EXISTS rolap.journal_communities")
        assignments_df.to_sql(
            "journal_communities",
            conn,
            schema="rolap",
            index=False,
            if_exists="replace",
        )
        logging.info(
            f"Saved {len(assignments_df)} community assignments to rolap.journal_communities"
        )

    if community_potential_df is not None:
        conn.execute("DROP TABLE IF EXISTS rolap.community_citation_potential")
        community_potential_df.to_sql(
            "community_citation_potential",
            conn,
            schema="rolap",
            index=False,
            if_exists="replace",
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
        default=SIMILARITY_THRESHOLD_MIN,
        help="Multi-assignment threshold",
    )
    parser.add_argument("--db", required=True, help="Path to the main SQLite database")
    parser.add_argument("--rolap-db", required=True, help="Path to the ROLAP SQLite database")
    args = parser.parse_args()

    try:
        conn = get_db_connection(args.db, args.rolap_db)

        publications_df, citations_df, reference_df = load_journal_data(conn)
        coupling_df = load_bibliographic_coupling(conn)

        if len(coupling_df) == 0:
            logging.warning("No bibliographic coupling data. Using fallback.")
            impact_df = calculate_context_impact_fallback(publications_df, citations_df, reference_df)
            save_results(conn, impact_df)
        else:
            g, journals, _ = build_graph(coupling_df)
            partition = run_leiden_clustering(g, resolution=args.resolution)

            assignments_df = assign_journals_to_communities(
                g,
                partition,
                journals,
                threshold_min=args.threshold,
                threshold_max=SIMILARITY_THRESHOLD_MAX,
            )

            community_potential_df = calculate_citation_potential(assignments_df, reference_df)
            journal_potential_df = calculate_journal_citation_potential(assignments_df, community_potential_df)

            impact_df = calculate_context_impact(publications_df, citations_df, journal_potential_df)
            save_results(conn, impact_df, assignments_df, community_potential_df)

        logging.info("Context-normalized impact calculation complete.")

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
