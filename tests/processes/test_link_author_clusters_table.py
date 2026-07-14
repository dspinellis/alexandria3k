# Konstantinos Tsesmelis
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2026  Diomidis Spinellis
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
"""link_and_table scoring function unit tests"""

import unittest

from ..test_dir import add_src_dir

add_src_dir()

from alexandria3k.processes.link_merged_author_table import (
    compare_authors,
    get_ngrams,
    jaccard_similarity,
    JaroWinkler
)
from alexandria3k.processes.link_author_blocks import normalized


class TestJaroWinkler(unittest.TestCase):
    def test_identical_strings(self):
        self.assertEqual(JaroWinkler.similarity("same", "same"), 1.0)

    def test_disjoint_strings(self):
        self.assertEqual(JaroWinkler.similarity("abc", "xyz"), 0.0)

    def test_known_reference_pair(self):
        # Standard textbook example (Winkler, 1990)
        self.assertAlmostEqual(
            JaroWinkler.similarity("martha", "marhta"), 0.9611111111111111
        )

    def test_one_empty_string(self):
        self.assertEqual(JaroWinkler.similarity("", "abc"), 0.0)

    def test_both_empty_strings(self):
        self.assertEqual(JaroWinkler.similarity("", ""), 1.0)


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical_sets(self):
        self.assertEqual(jaccard_similarity({1, 2, 3}, {1, 2, 3}), 1.0)

    def test_disjoint_sets(self):
        self.assertEqual(jaccard_similarity({1, 2}, {3, 4}), 0.0)

    def test_partial_overlap(self):
        self.assertEqual(jaccard_similarity({1, 2, 3}, {2, 3, 4}), 0.5)

    def test_both_sets_empty(self):
        self.assertEqual(jaccard_similarity(set(), set()), 0)

    def test_one_set_empty(self):
        self.assertEqual(jaccard_similarity({1, 2}, set()), 0)


class TestCompareAuthorsSameWorkId(unittest.TestCase):
    def test_same_work_id_never_matches(self):
        auth1 = (1, "yun", 555)
        auth2 = (2, "yun", 555)
        self.assertEqual(compare_authors(auth1, auth2, {}, {}, None), 0)

    def test_different_work_id_does_not_short_circuit(self):
        # work_id check.
        auth1 = (1, "yun", 555)
        auth2 = (2, "xyz", 999)
        self.assertEqual(compare_authors(auth1, auth2, {}, {}, None), 0)


class TestGetNgrams(unittest.TestCase):
    def test_single_word_has_no_bigrams_or_trigrams(self):
        self.assertEqual(get_ngrams("edinburgh"), {"edinburgh"})

    def test_two_words_has_unigrams_and_one_bigram_only(self):
        self.assertEqual(
            get_ngrams("university edinburgh"),
            {"university", "edinburgh", "university edinburgh"},
        )

    def test_three_words_has_1_2_3_grams(self):
        self.assertEqual(
            get_ngrams("university of edinburgh"),
            {
                "university",
                "of",
                "edinburgh",
                "university of",
                "of edinburgh",
                "university of edinburgh",
            },
        )

    def test_empty_string_has_no_ngrams(self):
        self.assertEqual(get_ngrams(""), set())

    def test_identical_text_gives_identical_ngram_sets(self):
        self.assertEqual(
            get_ngrams("roslin institute"), get_ngrams("roslin institute")
        )


class TestNormalized(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(normalized("JOHN"), "john")

    def test_strips_decomposable_diacritics(self):
        # NFKD decomposes accented letters into base + combining mark,
        # which is then stripped
        self.assertEqual(normalized("José"), "jose")

    def test_strips_punctuation_and_digits(self):
        self.assertEqual(normalized("O'Brien-123"), "obrien")

    def test_keeps_internal_spaces(self):
        self.assertEqual(normalized(" Jean Paul "), "jean paul")

    def test_stroke_letters_are_not_folded(self):
        self.assertEqual(normalized("Øystein"), "øystein")


if __name__ == "__main__":
    unittest.main()
