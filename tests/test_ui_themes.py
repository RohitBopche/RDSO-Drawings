"""Every theme must be readable: WCAG contrast for the colour pairs the pages actually use."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "ui" / "themes.css").read_text(encoding="utf-8")


def parse():
    themes = {}
    for m in re.finditer(r':root(?:, :root)?\[data-theme="([a-z-]+)"\]\s*\{(.*?)\}', CSS, re.S):
        themes[m.group(1)] = dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", m.group(2)))
    return themes


def lum(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PAIRS = [("ink", "bg"), ("ink", "surface"), ("ink", "surface2"), ("muted", "bg"), ("muted", "surface"), ("muted", "surface2"),
         ("accent", "bg"), ("accent", "surface"), ("accent-ink", "accent"), ("user-ink", "user"), ("chip-ink", "chip"),
         ("ok", "surface"), ("warn", "surface"), ("bad", "surface"), ("ink", "mark"), ("accent", "surface2")]


def test_expected_themes_exist():
    assert set(parse()) == {"light", "dark", "solarized-light", "solarized-dark", "paper", "nord", "signal", "contrast"}


@pytest.mark.parametrize("theme", sorted(parse()))
def test_theme_contrast(theme):
    t = parse()[theme]
    need = 7.0 if theme == "contrast" else 4.5
    bad = [(a, b, round(ratio(t[a], t[b]), 2)) for a, b in PAIRS if ratio(t[a], t[b]) < need]
    assert not bad, f"{theme}: {bad}"


def test_all_themes_define_the_same_variables():
    themes = parse()
    keys = set(themes["light"])
    for name, t in themes.items():
        assert set(t) >= {"bg", "surface", "ink", "muted", "line", "accent", "accent-ink", "user", "user-ink", "chip", "chip-ink", "mark", "ok", "warn", "bad"}, name
        assert set(t) == keys, (name, set(t) ^ keys)
