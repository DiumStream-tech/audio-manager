import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


_APP_DIR_NAME = "audiomanager"
_SETTINGS_FILENAME = "settings.json"


def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / _APP_DIR_NAME


def _settings_path() -> Path:
    return _config_dir() / _SETTINGS_FILENAME


def _default_data() -> Dict[str, Any]:
    return {
        "theme": "dark",
        "language": "en",
        "last_section": "outputs",
        "streaming": {
            "channels": {},
        },
        "routes": {
            "normal": {"playback": {}, "recording": {}},
            "streaming": {"playback": {}, "recording": {}},
        },
    }


class SettingsStore:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        data = _default_data()
        try:
            with open(_settings_path(), "r", encoding="utf-8") as f:
                on_disk = json.load(f)
        except (FileNotFoundError, ValueError, OSError):
            return data

        if not isinstance(on_disk, dict):
            return data

        theme_value = on_disk.get("theme")
        if isinstance(theme_value, str):
            data["theme"] = theme_value

        lang_value = on_disk.get("language")
        if isinstance(lang_value, str):
            data["language"] = lang_value

        last_section_value = on_disk.get("last_section")
        if isinstance(last_section_value, str):
            data["last_section"] = last_section_value

        streaming = on_disk.get("streaming")
        if isinstance(streaming, dict):
            channels = streaming.get("channels")
            if isinstance(channels, dict):
                data["streaming"]["channels"] = channels

        routes = on_disk.get("routes")
        if isinstance(routes, dict):
            for profile in ("normal", "streaming"):
                profile_routes = routes.get(profile)
                if not isinstance(profile_routes, dict):
                    continue
                for kind in ("playback", "recording"):
                    kind_routes = profile_routes.get(kind)
                    if isinstance(kind_routes, dict):
                        data["routes"][profile][kind] = kind_routes

        return data

    def _save(self):
        path = _settings_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_name(path.name + ".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(path)
        except OSError:
            pass

    def get_theme(self) -> str:
        return self._data.get("theme", "dark")

    def set_theme(self, theme_key: str):
        if self._data.get("theme") == theme_key:
            return
        self._data["theme"] = theme_key
        self._save()

    def get_last_section(self) -> str:
        return self._data.get("last_section", "outputs")

    def set_last_section(self, section_key: str):
        if self._data.get("last_section") == section_key:
            return
        self._data["last_section"] = section_key
        self._save()

    def get_channel_settings(self, channel_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get("streaming", {}).get("channels", {}).get(channel_id)

    def set_channel_settings(self, channel_id: str, values: Dict[str, Any]):
        channels = self._data.setdefault("streaming", {}).setdefault("channels", {})
        channels[channel_id] = values
        self._save()

    def _routes_profile(self, streaming_enabled: bool) -> str:
        return "streaming" if streaming_enabled else "normal"

    def get_stream_route(self, kind: str, app_name: str, streaming_enabled: bool) -> Optional[str]:
        profile = self._routes_profile(streaming_enabled)
        return self._data.get("routes", {}).get(profile, {}).get(kind, {}).get(app_name)

    def set_stream_route(self, kind: str, app_name: str, device_name: str, streaming_enabled: bool):
        profile = self._routes_profile(streaming_enabled)
        routes = (
            self._data.setdefault("routes", {})
            .setdefault(profile, {})
            .setdefault(kind, {})
        )
        if routes.get(app_name) == device_name:
            return
        routes[app_name] = device_name
        self._save()

    def get_language(self) -> str:
        return self._data.get("language", "en")

    def set_language(self, lang: str):
        if self._data.get("language") == lang:
            return
        self._data["language"] = lang
        self._save()


_settings_instance: Optional[SettingsStore] = None


def get_settings_store() -> SettingsStore:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsStore()
    return _settings_instance
