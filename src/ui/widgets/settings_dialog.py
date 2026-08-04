"""Settings dialog — redesigned for 0.0.3 with language support and changelog button."""

from PyQt6.QtCore import QThread, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import config, i18n
from src.core.updater import check_for_update
from src.ui import theme
from src.ui.icons import Icons


class _UpdateCheckWorker(QThread):
    finished_check = pyqtSignal(object)

    def run(self):
        self.finished_check.emit(check_for_update())


class SettingsDialog(QDialog):
    # Emitted when the user changes the language so the caller can rebuild UI
    language_changed = pyqtSignal(str)

    def __init__(self, current_theme_key: str, on_theme_change, parent=None):
        super().__init__(parent)
        self._on_theme_change = on_theme_change
        self._update_worker = None

        # Track action buttons for refresh: list of (btn, icon_name, i18n_key)
        self._action_buttons: list[tuple[QPushButton, str, str]] = []

        self.setWindowTitle(i18n.t("settings.title"))
        self.setFixedWidth(380)
        self.setModal(True)
        self.setObjectName("settingsDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("settingsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 14)
        header_layout.setSpacing(10)

        self._header_icon_lbl = QLabel()
        header_layout.addWidget(self._header_icon_lbl)

        self._title_lbl = QLabel(i18n.t("settings.title"))
        self._title_lbl.setObjectName("settingsTitle")
        header_layout.addWidget(self._title_lbl)
        header_layout.addStretch()

        root.addWidget(header)

        sep = QFrame()
        sep.setObjectName("settingsSep")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── Body ────────────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("settingsBody")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        # Section: Appearance
        self._lbl_appearance = self._section_label(i18n.t("settings.section_appearance"))
        layout.addWidget(self._lbl_appearance)
        layout.addSpacing(6)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("settingsThemeCombo")
        self.theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for key, lbl in theme.THEME_LABELS.items():
            self.theme_combo.addItem(lbl, key)
        current_idx = list(theme.THEME_LABELS.keys()).index(current_theme_key)
        self.theme_combo.setCurrentIndex(current_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        layout.addWidget(self.theme_combo)

        layout.addSpacing(18)

        # Section: Language
        self._lbl_language = self._section_label(i18n.t("settings.section_language"))
        layout.addWidget(self._lbl_language)
        layout.addSpacing(6)

        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName("settingsLangCombo")
        self.lang_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for code, lbl in i18n.SUPPORTED_LANGUAGES.items():
            self.lang_combo.addItem(lbl, code)
        current_lang_idx = list(i18n.SUPPORTED_LANGUAGES.keys()).index(i18n.get_language())
        self.lang_combo.setCurrentIndex(current_lang_idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_combo_changed)
        layout.addWidget(self.lang_combo)

        layout.addSpacing(18)

        # Section: GitHub & Updates
        self._lbl_github = self._section_label(i18n.t("settings.section_github"))
        layout.addWidget(self._lbl_github)
        layout.addSpacing(6)

        self.github_btn = self._action_button("github", "settings.open_github")
        self.github_btn.clicked.connect(self._open_github)
        self.github_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)
        layout.addWidget(self.github_btn)

        layout.addSpacing(6)

        self.update_btn = self._action_button("check_updates", "settings.check_updates")
        self.update_btn.clicked.connect(self._check_updates)
        self.update_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)
        layout.addWidget(self.update_btn)

        if not config.GITHUB_UPDATES_ENABLED:
            layout.addSpacing(8)
            self._note_lbl = QLabel(i18n.t("settings.updates_disabled_note"))
            self._note_lbl.setWordWrap(True)
            self._note_lbl.setProperty("role", "faint")
            self._note_lbl.setObjectName("settingsNote")
            layout.addWidget(self._note_lbl)
        else:
            self._note_lbl = None

        layout.addStretch()

        root.addWidget(body, 1)

        sep2 = QFrame()
        sep2.setObjectName("settingsSep")
        sep2.setFixedHeight(1)
        root.addWidget(sep2)

        # ── Footer ──────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("settingsFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 14)

        version_lbl = QLabel(f"v{config.APP_VERSION}")
        version_lbl.setObjectName("settingsVersion")
        version_lbl.setProperty("role", "faint")
        footer_layout.addWidget(version_lbl)

        footer_layout.addStretch()

        self._close_btn = QPushButton()
        self._close_btn.setObjectName("settingsCloseButton")
        self._close_btn.setProperty("variant", "dialog-close")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self._close_btn)

        root.addWidget(footer)

        # Initial render of icons/texts (uses current theme color)
        self._refresh_icons_and_texts()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("settingsSectionLabel")
        label.setProperty("role", "faint")
        return label

    def _action_button(self, icon_name: str, i18n_key: str) -> QPushButton:
        """Create an action button and register it for future refreshes."""
        btn = QPushButton()
        btn.setObjectName("settingsActionButton")
        btn.setProperty("variant", "settings-action")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(34)
        self._action_buttons.append((btn, icon_name, i18n_key))
        return btn

    def _refresh_icons_and_texts(self) -> None:
        """Re-apply icons with the current theme color and texts with the current language."""
        color = theme.TEXT

        # Header icon
        icon = Icons.get("settings", color=color)
        if icon:
            self._header_icon_lbl.setPixmap(icon.pixmap(20, 20))
            self._header_icon_lbl.show()
        else:
            self._header_icon_lbl.hide()

        # Header title
        self._title_lbl.setText(i18n.t("settings.title"))
        self.setWindowTitle(i18n.t("settings.title"))

        # Section labels
        self._lbl_appearance.setText(i18n.t("settings.section_appearance").upper())
        self._lbl_language.setText(i18n.t("settings.section_language").upper())
        self._lbl_github.setText(i18n.t("settings.section_github").upper())

        # Action buttons
        for btn, icon_name, i18n_key in self._action_buttons:
            Icons.apply_to_button(btn, icon_name, i18n.t(i18n_key), color=color)

        # Close button
        Icons.apply_to_button(self._close_btn, "close", i18n.t("settings.close"), color=color)

        # Note label
        if self._note_lbl is not None:
            self._note_lbl.setText(i18n.t("settings.updates_disabled_note"))

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_theme_combo_changed(self, index: int):
        key = self.theme_combo.itemData(index)
        self._on_theme_change(key)
        # Refresh icons immediately so they use the new theme color
        self._refresh_icons_and_texts()

    def _on_lang_combo_changed(self, index: int):
        code = self.lang_combo.itemData(index)
        if code != i18n.get_language():
            i18n.set_language(code)
            self._refresh_icons_and_texts()
            self.language_changed.emit(code)

    def _open_github(self):
        QDesktopServices.openUrl(QUrl(config.GITHUB_URL))

    def _open_changelog(self):
        from src.ui.widgets.changelog_dialog import ChangelogDialog
        dlg = ChangelogDialog(parent=self)
        dlg.exec()

    def _check_updates(self):
        self.update_btn.setEnabled(False)
        Icons.apply_to_button(self.update_btn, "checking", i18n.t("settings.checking"), color=theme.TEXT)

        self._update_worker = _UpdateCheckWorker(self)
        self._update_worker.finished_check.connect(self._on_update_check_done)
        self._update_worker.start()

    def _on_update_check_done(self, result):
        Icons.apply_to_button(self.update_btn, "check_updates", i18n.t("settings.check_updates"), color=theme.TEXT)
        self.update_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)

        if not result.ok:
            self._show_update_result_dialog(
                title=i18n.t("update.error_title"),
                message=i18n.t("update.error_body", error=result.error),
                icon_type="warning",
            )
            return

        if result.update_available:
            self._show_update_result_dialog(
                title=i18n.t("update.available_title"),
                message=i18n.t(
                    "update.available_body",
                    latest=result.latest_version,
                    current=result.current_version,
                ),
                icon_type="info",
                show_github_btn=True,
            )
        else:
            self._show_update_result_dialog(
                title=i18n.t("update.up_to_date_title"),
                message=i18n.t("update.up_to_date_body", current=result.current_version),
                icon_type="info",
            )

    def _show_update_result_dialog(
        self,
        title: str,
        message: str,
        icon_type: str = "info",
        show_github_btn: bool = False,
    ):
        from src.ui.widgets.update_result_dialog import UpdateResultDialog
        dlg = UpdateResultDialog(
            title=title,
            message=message,
            icon_type=icon_type,
            show_github_btn=show_github_btn,
            parent=self,
        )
        dlg.exec()
