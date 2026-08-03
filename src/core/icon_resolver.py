from urllib.parse import quote


ICON_API_PATTERNS = (
    "https://cdn.simpleicons.org/{slug}",
    "https://cdn.simpleicons.org/{slug}/{color}",
)


def resolve_icon_url(slug: str, color: str = "") -> str:
    slug = (slug or "").strip()
    color = (color or "").strip().lstrip("#")
    if not slug:
        return ""
    if color:
        return ICON_API_PATTERNS[1].format(
            slug=quote(slug, safe=""),
            color=quote(color, safe="")
        )
    return ICON_API_PATTERNS[0].format(slug=quote(slug, safe=""))