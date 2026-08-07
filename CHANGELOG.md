
# Changelog — Audio Manager

---

## [0.0.7] — 2026-08-07

### Refactoring & Architecture
- **Complete Style folder overhaul**: Removed `dialogs_style.py` and split `base_style.py` into 4 separate files (`base.py`, `buttons.py`, `components.py`, `pages.py`) for better maintainability.
- **Import cleanup**: Removed all `__init__.py` files across the project and updated imports to use explicit paths.
- **Style unification**: Centralized card styles (DeviceCard, StreamCard) in the global stylesheet via dynamic properties.

### Optimizations
- **Icon caching**: Implemented a caching system for FontAwesome icons to reduce CPU load during UI rendering.
- **UI rendering optimization**: Removed frequent `setStyleSheet` calls in widgets in favor of CSS property selectors, improving interface smoothness.
- **Code optimization**: Overall code cleanup and improved module structure.

### Fixed
- Fixed a bug where the navigation button to the Streaming page was not translated (present since v0.0.6).

---

## [0.0.6] — 2026-08-06

### Added
- **Full Navigation Unification**: Settings and Changelog pages are now identical to other sections (Outputs, Inputs, etc.).
- **Sidebar Reorganization**: Settings and Changelog buttons moved to the bottom of the sidebar, just above the Refresh button.
- Removed internal headers and footers from Settings and Changelog to better integrate with the main interface.

### Fixed
- Fixed a bug where changing language or theme would force navigation away from the Settings page.
- Restored audio safety (mute/unmute) when activating streaming mode, including during startup restoration.
- The Settings page now remains active after applying changes, providing a smoother user experience.

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

---

### 🔐 Verification

This release is signed with GPG. You can verify the authenticity of the executable before running it.

**Public key fingerprint:**
```
34C2C91E106AD7833D65785F1F5E959577226B2C
```

**Verify the signature:**
```bash
gpg --verify AudioManager.asc AudioManager
```

> If the verification fails or the fingerprint doesn't match, do **not** run the executable — it may have been tampered with.