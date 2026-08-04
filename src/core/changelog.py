from typing import Dict, List, Optional

CHANGELOG: Dict[str, Dict[str, List[str]]] = {
    "0.0.1": {
        "en": None,
        "fr": None,
        "es": None,
    },
    "0.0.2": {
        "en": None,
        "fr": None,
        "es": None,
    },
    "0.0.3": {
        "en": [
            "Added multi-language support (English and French and Spanish) — English is the default.",
            "Redesigned the Settings dialog with clearer sections and improved layout.",
            "Redesigned the update-check result dialog with a polished interface.",
            "Added a 'View Changelog' button under the Settings button.",
            "Introduced this Changelog dialog — you are reading it right now!",
        ],
        "fr": [
            "Ajout du système de langue (anglais, français et espagnol) — l'anglais est la langue par défaut.",
            "Refonte du menu Réglages avec des sections plus claires et une meilleure mise en page.",
            "Refonte du menu de vérification de mise à jour avec une interface améliorée.",
            "Ajout d'un bouton « Voir le changelog » sous le bouton des Réglages.",
            "Introduction de ce dialogue Changelog — tu es en train de le lire !",
        ],
        "es": [
            "Adición del sistema de idiomas (inglés, francés y español); el inglés es el idioma predeterminado.",
            "Rediseño del menú de Configuración con secciones más claras y un mejor diseño.",
            "Rediseño del menú de verificación de actualizaciones con una interfaz mejorada.",
            "Adición de un botón «Ver registro de cambios» debajo del botón de Configuración.",
            "Introducción de este cuadro de diálogo de registro de cambios — ¡lo estás leyendo ahora!"
        ]
    },
}

VERSION_ORDER: List[str] = ["0.0.1", "0.0.2", "0.0.3"]


def get_changes(version: str, lang: str = "en") -> Optional[List[str]]:
    """
    Return the list of change strings for *version* in *lang*.
    Returns None if the version is unknown or has no recorded changelog.
    Returns an empty list if the version is known but has no changes in the requested lang.
    """
    entry = CHANGELOG.get(version)
    if entry is None:
        return None
    result = entry.get(lang) or entry.get("en")
    return result


def has_changes(version: str) -> bool:
    """Return True if *version* has at least one recorded change in any language."""
    entry = CHANGELOG.get(version, {})
    return any(bool(v) for v in entry.values())
