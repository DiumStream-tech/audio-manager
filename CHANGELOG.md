# Changelog — Audio Manager

---

## [0.0.5] — 2026-08-06

### Added
- Settings and Changelog now open directly inside the main window — no more separate pop-up windows.
- Startup loading screen that restores saved state (settings, streaming button) before showing the interface.
- `STREAMING_SAVE_BUTTON_STATE` option in `config.py` — when enabled, the streaming mode button state is persisted across launches.
- `SPLASH_DURATION_MS` option in `config.py` — controls the duration of the startup loading screen.
- Full compatibility with the language system (i18n) for all new features (splash screen messages in EN/FR/ES).
- Version 0.0.5 release notes added to all three language changelogs.

---

## [0.0.4] — 2026-08-04

### Changed
- Refactored the codebase to improve structure and long-term maintainability.
- Reorganized several UI and core modules into dedicated folders for better clarity.

### Fixed
- Fixed missing translations across the interface.
- Fixed full compatibility with the language system (i18n) in dialogs, cards, streaming views, and the main window.
- Fixed multiple hardcoded UI texts that were not using the translation system.

---

## [0.0.3] — 2026-08-03

### Added
- Multi-language support (English and French and Spanish) — English is the default.
- Changelog dialog (this file's in-app counterpart) — accessible from the sidebar.
- "View Changelog" button under the Settings button.
- `i18n.py` module with a full translation system (`t()`, `set_language()`, `get_language()`).

### Changed
- Redesigned the Settings dialog with clearer sections (Appearance, Language, GitHub & Updates).
- Redesigned the update-check result dialog with a polished, consistent interface.
- Icons in the Settings dialog now correctly follow the active theme color (fixes white icons on the light theme).
- The Settings dialog now updates its texts and icons immediately when the language or theme is changed, without needing to close and reopen it.

### Fixed
- Icons in Settings were always rendered in white regardless of the active theme.

---

## [0.0.2] — *Changelog not available*

> The changelog feature was introduced in 0.0.3. No release notes were recorded for this version.

---

## [0.0.1] — *Changelog not available*

> The changelog feature was introduced in 0.0.3. No release notes were recorded for this version.