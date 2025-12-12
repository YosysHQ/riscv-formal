#!/usr/bin/env python3
from typing import Any

# -- Project information --------------

project = 'RISC-V Formal'
copyright = '2025, YosysHQ GmbH'
author = 'YosysHQ GmbH'

# -- General configuration ------------

extensions: list[str] = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_toolbox.more_autodoc.typevars',
    'sphinx_toolbox.more_autodoc.typehints',
]

# -- Options for HTML output ----------

html_theme = 'furo-ys'
html_static_path = ['_static']

html_css_files = ['custom.css']

html_theme_options: dict[str, Any] = {}

# -- Options for autosectionlabel -----

autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 1

# -- Options for autodoc --------------

autodoc_typehints = 'description'
autoclass_content = 'both'
autodoc_member_order = 'bysource'
autodoc_typehints_description_target = 'documented'

# -- Options for intersphinx ----------

intersphinx_mapping = {
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "py": ("https://docs.python.org/3", None),
}
