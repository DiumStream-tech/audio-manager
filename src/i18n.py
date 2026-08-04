"""
Internationalization (i18n) module for Audio Manager.

Translations live in src/langs/<lang>/<namespace>.json.
Files are loaded lazily on first access — only the namespaces actually
used at runtime are read from disk, and only once per language switch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "fr": "Français",
    "es": "Espagnol",

}

DEFAULT_LANGUAGE = "en"

def _get_langs_dir() -> Path:
    """
    Resolve the langs/ directory whether running from source or a PyInstaller bundle.
    In a bundle, PyInstaller extracts --add-data files under sys._MEIPASS.
    """
    import sys
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller onefile executable
        return Path(sys._MEIPASS) / "src" / "langs"
    # Running from source
    return Path(__file__).parent / "langs"

_LANGS_DIR = _get_langs_dir()

# ── Runtime state ─────────────────────────────────────────────────────────────

_current_language: str = DEFAULT_LANGUAGE

# Cache: { lang: { namespace: { key: value } } }
_cache: dict[str, dict[str, dict[str, str]]] = {}

# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_namespace(lang: str, namespace: str) -> dict[str, str]:
    """Load and cache a single namespace JSON file for *lang*."""
    if lang not in _cache:
        _cache[lang] = {}
    ns_cache = _cache[lang]
    if namespace not in ns_cache:
        path = _LANGS_DIR / lang / f"{namespace}.json"
        if path.exists():
            with path.open(encoding="utf-8") as f:
                ns_cache[namespace] = json.load(f)
        else:
            ns_cache[namespace] = {}
    return ns_cache[namespace]


def _lookup(key: str, lang: str) -> Optional[str]:
    """Return the raw translation string for *key* in *lang*, or None."""
    parts = key.split(".", 1)
    if len(parts) != 2:
        return None
    namespace, subkey = parts
    ns = _load_namespace(lang, namespace)
    return ns.get(subkey)


# ── Public API ────────────────────────────────────────────────────────────────

def set_language(lang: str) -> None:
    """Switch the active language. Unknown codes are silently ignored."""
    global _current_language
    if lang in SUPPORTED_LANGUAGES:
        _current_language = lang


def get_language() -> str:
    """Return the currently active language code (e.g. 'en' or 'fr')."""
    return _current_language


def t(key: str, **kwargs) -> str:
    """
    Translate *key* in the active language, interpolating **kwargs.

    Resolution order:
      1. Active language
      2. English fallback
      3. The key itself (so missing strings are visible but never crash)
    """
    text = _lookup(key, _current_language) or _lookup(key, DEFAULT_LANGUAGE) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def invalidate_cache(lang: Optional[str] = None) -> None:
    """
    Clear the translation cache.
    Pass a specific *lang* to only clear that language, or None to clear all.
    Useful after hot-reloading lang files during development.
    """
    if lang is None:
        _cache.clear()
    elif lang in _cache:
        del _cache[lang]
