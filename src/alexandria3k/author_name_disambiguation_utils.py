from itertools import groupby

import unicodedata

from rapidfuzz.distance import JaroWinkler

from sklearn.feature_extraction.text import CountVectorizer


# Adapted from uf-toolkit (https://github.com/hugginsc10/uf-toolkit)
# Copyright (c) Chas Huggins
# Licensed under the MIT License
class UnionFind:
    """UnionFind datastructure implementation taken from github used for merging authors together"""

    def __init__(self, size):
        self.parent = [i for i in range(size)]
        self.rank = [0] * size

    def find(self, i):
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, a, b):
        rootA = self.find(a)
        rootB = self.find(b)

        if rootA != rootB:
            # Union by rank
            if self.rank[rootA] < self.rank[rootB]:
                self.parent[rootA] = rootB
            elif self.rank[rootA] > self.rank[rootB]:
                self.parent[rootB] = rootA
            else:
                self.parent[rootB] = rootA
                self.rank[rootA] += 1
    def connected(self, a, b):
        return self.find(a) == self.find(b)

    def count_sets(self):
        return sum(1 for i in range(len(self.parent)) if i == self.parent[i])

    def get_set_elements(self, i):
        root = self.find(i)
        return [x for x in range(len(self.parent)) if self.find(x) == root]


def jaccard_similarity(set_a, set_b):
    """Custom jaccard similarity used for comparing authors"""
    if set_a and set_b:
        union = set_a | set_b
        jaccard = len(set_a & set_b) / len(union)
    else:
        jaccard = 0

    return jaccard

def normalized(s: str):
    """Custom normalization function used for normalizing author_names """
    tmp = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if unicodedata.category(c) != "Mn" and (c.isalpha() or c.isspace())
    )
    return tmp.lower().strip()




ngram = CountVectorizer(ngram_range=(1, 3)).build_analyzer()

def get_ngrams(text):
    return set(ngram(text))