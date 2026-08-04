import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

from src import config, i18n


UPDATE_CHECK_TIMEOUT_SECONDS = 6


@dataclass
class UpdateCheckResult:
    ok: bool
    update_available: bool = False
    current_version: str = ""
    latest_version: str = ""
    error: str = ""


def _parse_version(text: str):
    if not text:
        return None
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)$", text.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _repo_owner_and_name():
    parsed = urlparse(config.GITHUB_URL)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]


def check_for_update(timeout: int = UPDATE_CHECK_TIMEOUT_SECONDS) -> UpdateCheckResult:
    current = config.APP_VERSION
    current_tuple = _parse_version(current)
    if current_tuple is None:
        return UpdateCheckResult(
            ok=False,
            current_version=current,
            error=i18n.t("updater.bad_local_version", version=current),
        )

    owner, repo = _repo_owner_and_name()
    if not owner or not repo:
        return UpdateCheckResult(
            ok=False,
            current_version=current,
            error=i18n.t("updater.bad_github_url"),
        )

    api_url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    request = urllib.request.Request(
        api_url,
        headers={"User-Agent": config.HTTP_USER_AGENT},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            tags = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return UpdateCheckResult(ok=False, current_version=current, error=str(exc))

    if not isinstance(tags, list):
        return UpdateCheckResult(
            ok=False,
            current_version=current,
            error=i18n.t("updater.unexpected_response"),
        )

    best_tuple = None
    best_name = ""

    for tag in tags:
        name = tag.get("name", "") if isinstance(tag, dict) else ""
        parsed_tag = _parse_version(name)
        if parsed_tag is not None and (best_tuple is None or parsed_tag > best_tuple):
            best_tuple = parsed_tag
            best_name = name

    if best_tuple is None:
        return UpdateCheckResult(
            ok=True,
            current_version=current,
            latest_version="",
            update_available=False,
        )

    return UpdateCheckResult(
        ok=True,
        current_version=current,
        latest_version=best_name,
        update_available=best_tuple > current_tuple,
    )