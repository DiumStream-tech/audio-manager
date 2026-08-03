import json
from pathlib import Path


_DATA_PATH = Path(__file__).parent / "data" / "apps.json"


def _load_data() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_data = _load_data()
KNOWN_APPS = _data.get("known_apps", {})
STREAM_NAME_ALIASES = _data.get("stream_aliases", {})
IGNORED_BINARIES = set(_data.get("ignored_binaries", []))


def _normalize(s: str) -> str:
    return (
        (s or "")
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
        .replace(" ", "")
    )


def reload_registry() -> None:
    global _data, KNOWN_APPS, STREAM_NAME_ALIASES, IGNORED_BINARIES
    _data = _load_data()
    KNOWN_APPS = _data.get("known_apps", {})
    STREAM_NAME_ALIASES = _data.get("stream_aliases", {})
    IGNORED_BINARIES = set(_data.get("ignored_binaries", []))


def lookup(binary: str):
    if not binary:
        return None

    raw_key = binary.rsplit("/", 1)[-1].lower()
    if raw_key in IGNORED_BINARIES:
        return None

    key = _normalize(raw_key)
    for needle in sorted(KNOWN_APPS, key=len, reverse=True):
        if _normalize(needle) in key:
            return KNOWN_APPS[needle]
    return None


def resolve_stream_name(app_name: str):
    if not app_name:
        return False

    key = _normalize(app_name)

    if key in STREAM_NAME_ALIASES:
        canonical = STREAM_NAME_ALIASES[key]
        if canonical is None:
            return None
        return KNOWN_APPS.get(canonical, False)

    for alias_key, canonical in STREAM_NAME_ALIASES.items():
        if _normalize(alias_key) in key:
            if canonical is None:
                return None
            return KNOWN_APPS.get(canonical, False)

    for needle in sorted(KNOWN_APPS, key=len, reverse=True):
        if _normalize(needle) in key:
            return KNOWN_APPS[needle]

    return False


def detect_running_apps(exclude_pids):
    try:
        import psutil
    except ImportError:
        return []

    excluded = set(exclude_pids or [])
    found = {}

    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            pid = proc.info["pid"]
            if pid in excluded:
                continue

            name = proc.info.get("name") or ""
            exe = proc.info.get("exe") or ""
            info = lookup(exe) or lookup(name)
            if info is None:
                continue

            label = info.get("label") or name or exe or str(pid)
            found.setdefault(label, {
                "pid": pid,
                "binary": exe or name,
                "display_name": label,
                "icon_slug": info.get("slug", ""),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return list(found.values())