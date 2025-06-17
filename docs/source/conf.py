# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Image Crawler Utils'
copyright = '2025, AkihaTatsu'
author = 'AkihaTatsu'
release = '0.4.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx_toolbox.collapse',
]

autodoc_member_order = "groupwise"
autodoc_typehints = "description"

templates_path = ['_templates']
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'nodriver': ('https://ultrafunkamsterdam.github.io/nodriver/', None),
    'rich': ('https://rich.readthedocs.io/en/latest/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}
exclude_patterns = []

import sys, os
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "image_crawler_utils", "stations")))

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['../build/html']
html_context = {
    'display_github': True,
    'github_user': 'AkihaTatsu',
    'github_repo': 'Image-Crawler-Utils',
    'github_version': 'main/docs/source/',
}
