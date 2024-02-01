# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import datetime
import os
import sys
import toml

sys.path.append("../src")
sys.path.append("../src/alexandria3k")

# Fetch current project data from pyproject.toml
conf_dir_path = os.path.dirname(__file__)
toml_path = os.path.join(conf_dir_path, '..', 'pyproject.toml')
with open(toml_path, 'r') as toml_file:
    pyproject_data = toml.load(toml_file)


project = pyproject_data["project"]["name"]
author = pyproject_data["project"]["authors"][0]["name"]
version = pyproject_data["project"]["version"]
release = version
copyright = f"2022-{datetime.now().year}, {author}"

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
html_context = {
    "display_version": True,
    "release": release,
}
html_theme_options = {
    'description': 'Local relational access to openly-available publication data sets',
    'github_user': 'dspinellis',
    'github_repo': 'alexandria3k',
    'github_type': 'star',
    'github_count': 'true',
    # Add a custom sidebar template
    'extra_nav_links': {
        "Version: " + release: None
    }
}


man_pages = [
    ("cli", "a3k", "Process bibliographic data sources", ["Diomidis Spinellis"], 1)
]
