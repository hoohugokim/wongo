"""Shipped profile reference docs must not leave theme-linked fonts on styles
whose font the builder set literally: a w:asciiTheme/w:hAnsiTheme attribute
beats the literal w:ascii/w:hAnsi (see docs/docx-quirks.md), so headings
would render in Word's theme font (Aptos) under the `default` style."""
import re
import zipfile
from pathlib import Path

import pytest

PROFILES = sorted(Path("src/wongo/profiles").glob("*/assets/reference.docx"))
STYLE_RE = re.compile(r'<w:style [^>]*w:styleId="([^"]+)".*?</w:style>', re.S)
RFONTS_RE = re.compile(r"<w:rFonts([^/]*?)/>")
THEME_ATTRS = ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")


@pytest.mark.parametrize("ref", PROFILES, ids=[p.parent.parent.name for p in PROFILES])
def test_literal_fonts_are_not_shadowed_by_theme_attributes(ref):
    styles = zipfile.ZipFile(ref).read("word/styles.xml").decode()
    shadowed = []
    for m in STYLE_RE.finditer(styles):
        for rf in RFONTS_RE.findall(m.group(0)):
            if "w:ascii=" in rf and any(a in rf for a in THEME_ATTRS):
                shadowed.append(m.group(1))
    assert shadowed == [], f"{ref}: {shadowed}"


def test_version_is_consistent_across_pyproject_package_and_citation():
    import wongo

    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    citation = Path("CITATION.cff").read_text(encoding="utf-8")
    assert re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1) == wongo.__version__
    assert re.search(r"^version: (\S+)", citation, re.M).group(1) == wongo.__version__
