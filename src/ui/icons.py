from __future__ import annotations

from typing import Optional

try:
    import qtawesome as qta
    _QTA_AVAILABLE = True
except ImportError:
    _QTA_AVAILABLE = False

# i18n is imported lazily inside label() to avoid circular imports at module load
_ICON_MAP: dict[str, tuple[str, str, str | None]] = {
    # (fa_name, fallback_glyph, i18n_key_or_None)
    "outputs":          ("fa5s.chevron-right",  "▶",  "nav.outputs"),
    "inputs":           ("fa5s.chevron-left",   "◀",  "nav.inputs"),
    "playback":         ("fa5s.music",          "♪",  "nav.playback"),
    "recording":        ("fa5s.record-vinyl",   "●",  "nav.recording"),
    "streaming":        ("fa5s.satellite-dish", "📡", "nav.streaming"),

    "settings":         ("fa5s.cog",            "⚙",  "main.sidebar_settings"),
    "refresh":          ("fa5s.sync-alt",       "↻",  "main.sidebar_refresh"),

    "volume_up":        ("fa5s.volume-up",      "🔊", None),
    "volume_mute":      ("fa5s.volume-mute",    "🔇", None),
    "microphone":       ("fa5s.microphone",     "🎙", None),
    "headphones":       ("fa5s.headphones",     "🎧", None),

    "streaming_start":  ("fa5s.play",           "▶",  "icon.streaming_start"),
    "streaming_stop":   ("fa5s.stop",           "⏹",  "icon.streaming_stop"),

    "link":             ("fa5s.link",           "🔗", "icon.link"),
    "unlink":           ("fa5s.unlink",         "✂",  "icon.unlink"),

    "channel_game":     ("fa5s.gamepad",        "🎮", "icon.channel_game"),
    "channel_chat":     ("fa5s.comments",       "💬", "icon.channel_chat"),
    "channel_media":    ("fa5s.globe",           "🌐", "icon.channel_media"),
    "channel_music":    ("fa5s.compact-disc",   "🎶", "icon.channel_music"),
    "channel_mic_aux":  ("fa5s.microphone-alt", "🎙️", "icon.channel_mic_aux"),

    "github":           ("fa5b.github",         "⎔",  "settings.open_github"),
    "check_updates":    ("fa5s.redo",           "↺",  "settings.check_updates"),
    "checking":         ("fa5s.sync-alt",       "…",  "settings.checking"),
    "close":            ("fa5s.times",          "✕",  None),
    "changelog":        ("fa5s.list-alt",       "📋", "changelog.title"),
    "warning":          ("fa5s.exclamation-triangle", "⚠", None),
}


def _color_kwargs(color: Optional[str]) -> dict:
    return {"color": color} if color else {}


def get(name: str, color: Optional[str] = None):
    if not _QTA_AVAILABLE:
        return None
    entry = _ICON_MAP.get(name)
    if entry is None:
        return None
    fa_name = entry[0]
    try:
        return qta.icon(fa_name, **_color_kwargs(color))
    except Exception:
        return None


def fallback(name: str) -> str:
    entry = _ICON_MAP.get(name)
    return entry[1] if entry else "?"


def label(name: str) -> str:
    entry = _ICON_MAP.get(name)
    if not entry:
        return name
    i18n_key = entry[2]
    if i18n_key:
        from src import i18n as _i18n
        return _i18n.t(i18n_key)
    return name


def apply_to_button(btn, name: str, text: str = "", color: Optional[str] = None) -> None:
    icon = get(name, color)
    if icon is not None:
        btn.setIcon(icon)
        btn.setText(f" {text}" if text else "")
    else:
        glyph = fallback(name)
        btn.setText(f"{glyph} {text}" if text else glyph)


class _Icons:
    get = staticmethod(get)
    fallback = staticmethod(fallback)
    label = staticmethod(label)
    apply_to_button = staticmethod(apply_to_button)


Icons = _Icons()
