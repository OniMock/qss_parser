import os
import sys
import tomlkit

sys.path.insert(0, os.path.abspath("../../src"))


def get_version():
    pyproject_path = os.path.abspath("../../pyproject.toml")
    try:
        with open(pyproject_path, "r", encoding="utf-8") as f:
            data = tomlkit.parse(f.read())
        version = data.get("project", {}).get("version", "0.0.0")
        return version
    except (FileNotFoundError, KeyError):
        return "0.0.0"


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

full_version = get_version()
version = str(".".join(full_version.split(".")[:2]))
release = str(full_version)

project = "QSS Parser"
copyright = "2025, OniMock"
author = "OniMock"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns = ["modules.rst"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = [""]
autodoc_member_order = "groupwise"


def skip(app, what, name, obj, skip, options):
    if name == "__init__":
        return False
    return skip


def process_docstring(app, what, name, obj, options, lines):
    # Strip the 'qss_parser.qss_parser.' prefix from docstrings
    for i in range(len(lines)):
        lines[i] = lines[i].replace("qss_parser.qss_parser.", "")


def setup(app):
    app.connect("autodoc-skip-member", skip)
    app.connect("autodoc-process-docstring", process_docstring)
