# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os

sys.path.append("../src")
sys.path.append("../src/alexandria3k")

project = "alexandria3k"
copyright = "2022-2023, Diomidis Spinellis"
author = "Diomidis Spinellis"
release = "2.5.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinxarg.ext"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Change html_static_path to an empty list because
# it was raising an issue, making the navigation bar
# in some pages not to work properly.
html_theme = "alabaster"
html_static_path = []

man_pages = [
    ("cli", "a3k", "Process bibliographic data sources", ["Diomidis Spinellis"], 1)
]
