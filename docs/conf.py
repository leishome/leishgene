import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "leishgene"
copyright = "2026"
author = "cokelaer"
release = "0.1.0"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
exclude_patterns = ["_build"]
master_doc = "index"
html_theme = "sphinx_rtd_theme"
autodoc_mock_imports = ["leishref", "rich_click", "rich"]
autodoc_default_options = {"members": True, "member-order": "bysource"}
