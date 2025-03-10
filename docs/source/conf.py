#!/usr/bin/env python3
project = 'RISC-V Formal'
copyright = '2025, YosysHQ GmbH'
author = 'YosysHQ GmbH'

# select HTML theme
html_theme = 'furo-ys'
html_css_files = ['custom.css']
html_theme_options: dict[str, any] = {}

# These folders are copied to the documentation's HTML output
html_static_path = ['_static']

# generate section labels from their heading
extensions = ['sphinx.ext.autosectionlabel']

# ensure that autosectionlabel will produce unique names
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 1
