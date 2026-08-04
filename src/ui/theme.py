THEMES = {
    "dark": {
        "BG": "#171717",
        "PANEL": "#1d1d1f",
        "PANEL_ALT": "#232326",
        "HOVER": "#2a2a2e",
        "BORDER": "#313136",
        "BORDER_SOFT": "#26262a",
        "BORDER_STRONG": "#3b3b42",
        "TEXT": "#f3f3f1",
        "TEXT_DIM": "#aaaaaf",
        "TEXT_FAINT": "#7b7b84",
        "TEXT_ON_ACCENT": "#101014",
        "AMBER": "#e3a53d",
        "AMBER_DIM": "#3d301a",
        "CYAN": "#49c8c0",
        "CYAN_DIM": "#173638",
        "DANGER": "#e5484d",
        "DANGER_DIM": "#3a1a1c",
        "GREEN": "#4ade80",
        "GREEN_DIM": "#1a3a25",
        "GRAY_LED": "#5b5b63",
        "SHADOW": "rgba(0, 0, 0, 0.28)",
    },
    "light": {
        "BG": "#f0f0f2",
        "PANEL": "#ffffff",
        "PANEL_ALT": "#e8e8ec",
        "HOVER": "#dcdce4",
        "BORDER": "#c8c8d0",
        "BORDER_SOFT": "#dcdce4",
        "BORDER_STRONG": "#b0b0bc",
        "TEXT": "#111116",
        "TEXT_DIM": "#555560",
        "TEXT_FAINT": "#88888f",
        "TEXT_ON_ACCENT": "#ffffff",
        "AMBER": "#c47c10",
        "AMBER_DIM": "#fdefd0",
        "CYAN": "#0a8f88",
        "CYAN_DIM": "#cdf0ee",
        "DANGER": "#cc2929",
        "DANGER_DIM": "#fce8e8",
        "GREEN": "#1a9e4a",
        "GREEN_DIM": "#d4f5e2",
        "GRAY_LED": "#aaaabc",
        "SHADOW": "rgba(17, 17, 22, 0.12)",
    },
}

THEME_LABELS = {
    "dark": "Sombre",
    "light": "Clair",
}

_current = "dark"

FONT_UI = "'Inter', 'Segoe UI', 'Ubuntu', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Mono', Consolas, Menlo, monospace"


def _apply():
    t = THEMES[_current]
    g = globals()
    for k, v in t.items():
        g[k] = v
    g["STATE_LED"] = {
        "running": g["GREEN"],
        "idle": "#d9b64a" if _current != "cyberpunk" else "#facc15",
        "suspended": g["GRAY_LED"],
        "unknown": g["GRAY_LED"],
    }


def set_theme(name: str):
    global _current
    if name in THEMES:
        _current = name
        _apply()


def current_theme() -> str:
    return _current


def accent_for(is_input: bool) -> str:
    return CYAN if is_input else AMBER


def accent_dim_for(is_input: bool) -> str:
    return CYAN_DIM if is_input else AMBER_DIM


_apply()
