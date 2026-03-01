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

"""Tests for the journal network metrics calculation module.

These are generic, eigenvector-centrality-based metrics that resemble well-known
third-party metrics, but are named generically in this codebase.
"""

import numpy as np
import pandas as pd
import pytest

from journal_network_metrics import (
    calculate_metric,
    calculate_network_centrality,
    calculate_prestige_rank,
    calculate_mean_article_score,
)


# =============================================================================
# NETWORK CENTRALITY TESTS
# =============================================================================


def check_centrality_ring(result: pd.DataFrame) -> None:
    """In a symmetric 3-node ring, all journals get equal scores."""
    scores = result.set_index("journal_id")["centrality_score"]
    assert np.isclose(scores[1], 33.333, atol=0.1)
    assert np.isclose(scores[2], 33.333, atol=0.1)
    assert np.isclose(scores[3], 33.333, atol=0.1)


def check_centrality_self_citation_removed(result: pd.DataFrame) -> None:
    """Self-citations are excluded for network centrality."""
    scores = result.set_index("journal_id")["centrality_score"]
    assert scores[2] > scores[1]


def check_centrality_disconnected(result: pd.DataFrame) -> None:
    """Two equal disconnected components distribute score evenly."""
    scores = result.set_index("journal_id")["centrality_score"]
    assert np.allclose(scores.values, 25.0, atol=0.2)


@pytest.mark.parametrize(
    "citations_data,journal_article_counts,expected_len,expected_sum,custom_check",
    [
        (
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            100.0,
            check_centrality_ring,
        ),
        (
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            100.0,
            None,
        ),
        (
            {
                "citing_journal": [1, 1],
                "cited_journal": [1, 2],
                "citation_count": [100, 10],
            },
            {1: 10, 2: 10},
            2,
            100.0,
            check_centrality_self_citation_removed,
        ),
        (
            {
                "citing_journal": [1, 2, 3, 4],
                "cited_journal": [2, 1, 4, 3],
                "citation_count": [10, 10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10, 4: 10},
            4,
            100.0,
            check_centrality_disconnected,
        ),
        (
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            0.0,
            None,
        ),
    ],
)
def test_calculate_network_centrality(
    citations_data,
    journal_article_counts,
    expected_len,
    expected_sum,
    custom_check,
):
    citations_df = pd.DataFrame(citations_data)
    result = calculate_network_centrality(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "centrality_score" in result.columns

    if not result.empty:
        assert np.isclose(result["centrality_score"].sum(), expected_sum, atol=0.5)
    else:
        assert expected_sum == 0.0

    if custom_check:
        custom_check(result)


# =============================================================================
# PRESTIGE RANK TESTS
# =============================================================================


def check_prestige_ring(result: pd.DataFrame) -> None:
    scores = result.set_index("journal_id")["prestige_score"]
    assert np.isclose(scores[1], 1.0, atol=0.1)
    assert np.isclose(scores[2], 1.0, atol=0.1)
    assert np.isclose(scores[3], 1.0, atol=0.1)


def check_prestige_self_citation_capped(result: pd.DataFrame) -> None:
    scores = result.set_index("journal_id")["prestige_score"]
    assert scores[1] > 0
    assert scores[2] > 0
    assert scores[1] > scores[2]


def check_prestige_disconnected(result: pd.DataFrame) -> None:
    scores = result.set_index("journal_id")["prestige_score"]
    assert np.allclose(scores.values, 1.0, atol=0.1)


def check_prestige_per_article_normalization(result: pd.DataFrame) -> None:
    scores = result.set_index("journal_id")["prestige_score"]
    assert scores[2] > scores[1]


@pytest.mark.parametrize(
    "citations_data,journal_article_counts,expected_len,custom_check",
    [
        (
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            check_prestige_ring,
        ),
        (
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            None,
        ),
        (
            {
                "citing_journal": [1, 1],
                "cited_journal": [1, 2],
                "citation_count": [100, 10],
            },
            {1: 10, 2: 10},
            2,
            check_prestige_self_citation_capped,
        ),
        (
            {
                "citing_journal": [1, 2, 3, 4],
                "cited_journal": [2, 1, 4, 3],
                "citation_count": [10, 10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10, 4: 10},
            4,
            check_prestige_disconnected,
        ),
        (
            {
                "citing_journal": [1, 2],
                "cited_journal": [2, 1],
                "citation_count": [100, 100],
            },
            {1: 100, 2: 10},
            2,
            check_prestige_per_article_normalization,
        ),
        (
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            None,
        ),
    ],
)
def test_calculate_prestige_rank(
    citations_data,
    journal_article_counts,
    expected_len,
    custom_check,
):
    citations_df = pd.DataFrame(citations_data)
    result = calculate_prestige_rank(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "prestige_score" in result.columns

    if custom_check:
        custom_check(result)


# =============================================================================
# MEAN ARTICLE SCORE TESTS
# =============================================================================


def check_mean_article_ring(result: pd.DataFrame) -> None:
    scores = result.set_index("journal_id")["mean_score"]
    assert np.isclose(scores[1], 1.0, atol=0.1)
    assert np.isclose(scores[2], 1.0, atol=0.1)
    assert np.isclose(scores[3], 1.0, atol=0.1)


@pytest.mark.parametrize(
    "citations_data,journal_article_counts,expected_len,custom_check",
    [
        (
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            check_mean_article_ring,
        ),
        (
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            None,
        ),
        (
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            None,
        ),
    ],
)
def test_calculate_mean_article_score(
    citations_data,
    journal_article_counts,
    expected_len,
    custom_check,
):
    citations_df = pd.DataFrame(citations_data)
    result = calculate_mean_article_score(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "mean_score" in result.columns

    if custom_check:
        custom_check(result)


def test_calculate_metric_rejects_unknown_metric():
    citations_df = pd.DataFrame(
        {
            "citing_journal": [1],
            "cited_journal": [2],
            "citation_count": [1],
        }
    )
    with pytest.raises(ValueError):
        calculate_metric(citations_df, {1: 1, 2: 1}, metric="unknown")
