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
"""
Calculate SNIP (Source Normalized Impact per Paper) using Leiden clustering.

SNIP normalizes a journal's citation impact by the citation potential of its
field. Fields are discovered through Leiden community detection on the
bibliographic coupling network.

Algorithm:
1. Build bibliographic coupling graph (journals sharing references)
2. Run Leiden clustering to discover research communities
3. Assign each journal to multiple communities (within 30-40% of max similarity)
4. Calculate citation potential per community
5. Compute each journal's weighted citation potential
6. SNIP = Raw Impact per Paper / Citation Potential

Key differences from seeded clustering:
- No pre-defined seeds that bias toward high-citation fields
- Communities emerge organically from citation patterns
- Handles interdisciplinary journals via multi-community assignment
- Uses Leiden algorithm (better than Louvain) for modularity optimization

Usage:
    ./snip.py                    # Calculate SNIP scores
    ./snip.py --resolution 1.0   # Adjust clustering resolution

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Constants
DEFAULT_RESOLUTION = 1.0
SIMILARITY_THRESHOLD_MIN = 0.30  # Minimum 30% of max similarity for multi-assignment
SIMILARITY_THRESHOLD_MAX = 0.40  # Maximum 40% of max similarity
MIN_COMMUNITY_SIZE = 3  # Minimum journals per community


def get_db_connection():
    """
    Establish connection to the main database and attach the ROLAP database.
    """
    main_db_path = os.environ.get("MAINDB", "impact")
    rolap_db_path = os.environ.get("ROLAPDB", "rolap")

    db_file = f"{main_db_path}.db"
    if not os.path.exists(db_file):
        if main_db_path == "impact" and os.path.exists("/tmp/impact.db"):
            db_file = "/tmp/impact.db"
        elif not os.path.exists(db_file):
            logging.critical(f"Main database file '{db_file}' not found.")
            raise FileNotFoundError(f"Database file '{db_file}' not found.")

    logging.info(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)

    rolap_file = f"{rolap_db_path}.db"
    logging.info(f"Attaching {rolap_file} as rolap...")
    conn.execute(f"ATTACH DATABASE '{rolap_file}' AS rolap")

    return conn


def load_bibliographic_coupling(conn):
    """
    Load the bibliographic coupling graph from the database.

    Returns:
        pd.DataFrame with columns: journal_a, journal_b, coupling_strength
    """
    logging.info("Loading bibliographic coupling data...")
    query = """
        SELECT journal_a, journal_b, coupling_strength
        FROM rolap.bibliographic_coupling
    """
    coupling_df = pd.read_sql_query(query, conn)
    logging.info(f"Loaded {len(coupling_df)} coupling edges.")
    return coupling_df


def load_journal_data(conn):
    """
    Load journal publication and citation data for SNIP calculation.

    Returns:
        tuple: (publications_df, citations_df)
    """
    logging.info("Loading journal publication data (3-year window)...")

    # Publications in the 3-year window
    publications_query = """
        SELECT journal_id, publications_number
        FROM rolap.publications3
    """
    publications_df = pd.read_sql_query(publications_query, conn)

    # Citations received (3-year window)
    citations_query = """
        SELECT cited_journal AS journal_id, SUM(citation_count) AS citations
        FROM rolap.citation_network3
        GROUP BY cited_journal
    """
    citations_df = pd.read_sql_query(citations_query, conn)

    # Reference density (average references per article)
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
    """
    Build an igraph Graph from the coupling DataFrame.

    Args:
        coupling_df: DataFrame with journal_a, journal_b, coupling_strength

    Returns:
        ig.Graph: Weighted undirected graph
    """
    logging.info("Building bibliographic coupling graph...")

    # Get unique journals
    journals = sorted(
        set(coupling_df["journal_a"]).union(set(coupling_df["journal_b"]))
    )
    journal_to_idx = {j: i for i, j in enumerate(journals)}

    # Create edge list
    edges = [
        (journal_to_idx[row["journal_a"]], journal_to_idx[row["journal_b"]])
        for _, row in coupling_df.iterrows()
    ]
    weights = coupling_df["coupling_strength"].values.tolist()

    # Build graph
    g = ig.Graph(n=len(journals), edges=edges, directed=False)
    g.vs["journal_id"] = journals
    g.es["weight"] = weights

    logging.info(f"Graph has {g.vcount()} vertices and {g.ecount()} edges.")
    return g, journals, journal_to_idx


def run_leiden_clustering(g, resolution=DEFAULT_RESOLUTION):
    """
    Run Leiden community detection on the graph.

    Args:
        g: igraph Graph
        resolution: Resolution parameter (higher = more communities)

    Returns:
        leidenalg.VertexPartition: Community partition
    """
    logging.info(f"Running Leiden clustering (resolution={resolution})...")

    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=resolution,
        n_iterations=-1,  # Run until convergence
        seed=42,  # Reproducibility
    )

    n_communities = len(partition)
    logging.info(f"Found {n_communities} communities.")

    # Log community size distribution
    sizes = [len(c) for c in partition]
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
    """
    Assign each journal to multiple communities based on coupling similarity.

    A journal is assigned to a community if its coupling strength to that
    community is within 30-40% of its maximum coupling strength (to its
    primary community).

    Args:
        g: igraph Graph
        partition: Leiden partition
        journals: List of journal IDs
        threshold_min: Minimum fraction of max similarity for assignment
        threshold_max: Maximum fraction (unused, kept for API consistency)

    Returns:
        pd.DataFrame: journal_id, community_id, weight (normalized)
    """
    logging.info("Assigning journals to communities (multi-assignment)...")

    # Calculate each journal's coupling strength to each community
    journal_community_strength = []

    for vertex_idx, journal_id in enumerate(journals):
        # Get neighbors and their weights
        neighbors = g.neighbors(vertex_idx)
        neighbor_weights = [g.es[g.get_eid(vertex_idx, n)]["weight"] for n in neighbors]

        # Sum coupling strength to each community
        community_strengths = {}
        for neighbor_idx, weight in zip(neighbors, neighbor_weights):
            community_id = partition.membership[neighbor_idx]
            community_strengths[community_id] = (
                community_strengths.get(community_id, 0) + weight
            )

        if not community_strengths:
            # Isolated journal - assign to own singleton community
            own_community = partition.membership[vertex_idx]
            journal_community_strength.append(
                {
                    "journal_id": journal_id,
                    "community_id": own_community,
                    "strength": 1.0,
                }
            )
            continue

        # Find maximum strength
        max_strength = max(community_strengths.values())
        threshold = max_strength * threshold_min

        # Assign to all communities above threshold
        for community_id, strength in community_strengths.items():
            if strength >= threshold:
                journal_community_strength.append(
                    {
                        "journal_id": journal_id,
                        "community_id": community_id,
                        "strength": strength,
                    }
                )

    assignments_df = pd.DataFrame(journal_community_strength)

    # Normalize weights per journal (sum to 1)
    total_per_journal = assignments_df.groupby("journal_id")["strength"].transform(
        "sum"
    )
    assignments_df["weight"] = assignments_df["strength"] / total_per_journal

    n_multi = (assignments_df.groupby("journal_id").size() > 1).sum()
    logging.info(
        f"Assigned journals to communities: {len(assignments_df)} total assignments."
    )
    logging.info(f"Journals with multiple community assignments: {n_multi}")

    return assignments_df[["journal_id", "community_id", "weight"]]


def calculate_citation_potential(assignments_df, reference_df):
    """
    Calculate citation potential for each community.

    Citation potential = average reference density of journals in the community,
    weighted by their publication output.

    Args:
        assignments_df: Journal-community assignments with weights
        reference_df: Journal reference density data

    Returns:
        pd.DataFrame: community_id, citation_potential
    """
    logging.info("Calculating citation potential per community...")

    # Merge reference data
    merged = assignments_df.merge(reference_df, on="journal_id", how="left")

    # Fill missing reference data with median
    median_refs = reference_df["avg_references"].median()
    merged["avg_references"] = merged["avg_references"].fillna(median_refs)

    # Weighted average reference density per community
    merged["weighted_refs"] = merged["avg_references"] * merged["weight"]
    community_potential = (
        merged.groupby("community_id")
        .agg(
            {
                "weighted_refs": "sum",
                "weight": "sum",
            }
        )
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
    """
    Calculate weighted citation potential for each journal.

    A journal's citation potential is the weighted average of its communities'
    citation potentials.

    Args:
        assignments_df: Journal-community assignments with weights
        community_potential_df: Citation potential per community

    Returns:
        pd.DataFrame: journal_id, citation_potential
    """
    logging.info("Calculating journal-level citation potential...")

    # Merge community potentials
    merged = assignments_df.merge(community_potential_df, on="community_id", how="left")

    # Weighted average citation potential per journal
    merged["weighted_potential"] = merged["citation_potential"] * merged["weight"]
    journal_potential = (
        merged.groupby("journal_id")["weighted_potential"].sum().reset_index()
    )
    journal_potential.columns = ["journal_id", "citation_potential"]

    logging.info(
        f"Calculated citation potential for {len(journal_potential)} journals."
    )

    return journal_potential


def calculate_snip(publications_df, citations_df, journal_potential_df):
    """
    Calculate SNIP for each journal.

    SNIP = Raw Impact per Paper / Citation Potential

    where Raw Impact per Paper = Citations / Publications (3-year window)

    Args:
        publications_df: Journal publication counts
        citations_df: Journal citation counts
        journal_potential_df: Journal citation potentials

    Returns:
        pd.DataFrame: journal_id, snip_score, raw_impact, citation_potential
    """
    logging.info("Calculating SNIP scores...")

    # Merge all data
    result = publications_df.merge(citations_df, on="journal_id", how="left")
    result = result.merge(journal_potential_df, on="journal_id", how="left")

    # Fill missing values
    result["citations"] = result["citations"].fillna(0)

    # Calculate Raw Impact per Paper
    result["raw_impact"] = result["citations"] / result["publications_number"]
    result["raw_impact"] = result["raw_impact"].replace([np.inf, -np.inf], 0)

    # Calculate SNIP
    result["snip_score"] = result["raw_impact"] / result["citation_potential"]
    result["snip_score"] = result["snip_score"].replace([np.inf, -np.inf], 0)
    result["snip_score"] = result["snip_score"].fillna(0)

    # Round to reasonable precision
    result["snip_score"] = result["snip_score"].round(3)
    result["raw_impact"] = result["raw_impact"].round(3)
    result["citation_potential"] = result["citation_potential"].round(3)

    logging.info(f"Calculated SNIP for {len(result)} journals.")
    logging.info(
        f"SNIP statistics: min={result['snip_score'].min():.3f}, "
        f"max={result['snip_score'].max():.3f}, "
        f"median={result['snip_score'].median():.3f}"
    )

    return result[["journal_id", "snip_score", "raw_impact", "citation_potential"]]


def calculate_snip_fallback(publications_df, citations_df, reference_df):
    """
    Fallback SNIP calculation when Leiden clustering is not available.

    Uses a simpler field-independent normalization based on the global
    average citation potential.

    Args:
        publications_df: Journal publication counts
        citations_df: Journal citation counts
        reference_df: Journal reference density data

    Returns:
        pd.DataFrame: journal_id, snip_score, raw_impact, citation_potential
    """
    logging.warning("Using fallback SNIP calculation (no community detection).")

    # Merge all data
    result = publications_df.merge(citations_df, on="journal_id", how="left")
    result = result.merge(reference_df, on="journal_id", how="left")

    # Fill missing values
    result["citations"] = result["citations"].fillna(0)
    median_refs = reference_df["avg_references"].median()
    result["avg_references"] = result["avg_references"].fillna(median_refs)

    # Use reference density as citation potential (global normalization)
    result["citation_potential"] = result["avg_references"]

    # Calculate Raw Impact per Paper
    result["raw_impact"] = result["citations"] / result["publications_number"]
    result["raw_impact"] = result["raw_impact"].replace([np.inf, -np.inf], 0)

    # Calculate SNIP
    result["snip_score"] = result["raw_impact"] / result["citation_potential"]
    result["snip_score"] = result["snip_score"].replace([np.inf, -np.inf], 0)
    result["snip_score"] = result["snip_score"].fillna(0)

    # Round to reasonable precision
    result["snip_score"] = result["snip_score"].round(3)
    result["raw_impact"] = result["raw_impact"].round(3)
    result["citation_potential"] = result["citation_potential"].round(3)

    logging.info(f"Calculated SNIP (fallback) for {len(result)} journals.")

    return result[["journal_id", "snip_score", "raw_impact", "citation_potential"]]


def save_results(conn, snip_df, assignments_df=None, community_potential_df=None):
    """
    Save SNIP results and intermediate data to the database.

    Args:
        conn: Database connection
        snip_df: SNIP scores
        assignments_df: Journal-community assignments (optional)
        community_potential_df: Community citation potentials (optional)
    """
    logging.info("Saving results to database...")

    # Save SNIP scores
    conn.execute("DROP TABLE IF EXISTS rolap.snip")
    snip_df.to_sql("snip", conn, schema="rolap", index=False, if_exists="replace")
    logging.info(f"Saved {len(snip_df)} SNIP scores to rolap.snip")

    # Save community assignments if available
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

    # Save community citation potentials if available
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
        description="Calculate SNIP using Leiden community detection."
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=DEFAULT_RESOLUTION,
        help=f"Leiden resolution parameter (default: {DEFAULT_RESOLUTION})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD_MIN,
        help=f"Multi-assignment threshold (default: {SIMILARITY_THRESHOLD_MIN})",
    )
    args = parser.parse_args()

    try:
        conn = get_db_connection()

        # Load data
        publications_df, citations_df, reference_df = load_journal_data(conn)

        # Load bibliographic coupling
        coupling_df = load_bibliographic_coupling(conn)

        if len(coupling_df) == 0:
            logging.warning("No bibliographic coupling data. Using fallback.")
            snip_df = calculate_snip_fallback(
                publications_df, citations_df, reference_df
            )
            save_results(conn, snip_df)
        else:
            # Build graph and run clustering
            g, journals, journal_to_idx = build_graph(coupling_df)
            partition = run_leiden_clustering(g, resolution=args.resolution)

            # Assign journals to communities
            assignments_df = assign_journals_to_communities(
                g, partition, journals, threshold_min=args.threshold
            )

            # Calculate citation potentials
            community_potential_df = calculate_citation_potential(
                assignments_df, reference_df
            )
            journal_potential_df = calculate_journal_citation_potential(
                assignments_df, community_potential_df
            )

            # Calculate SNIP
            snip_df = calculate_snip(
                publications_df, citations_df, journal_potential_df
            )

            # Save results
            save_results(conn, snip_df, assignments_df, community_potential_df)

        conn.close()
        logging.info("SNIP calculation complete.")

    except Exception as e:
        logging.error(f"Error calculating SNIP: {e}")
        raise


if __name__ == "__main__":
    main()
