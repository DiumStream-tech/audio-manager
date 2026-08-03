from PyQt6.QtCore import QThread, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QComboBox, QDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout

from src import config
from src.core.updater import check_for_update
from src.ui import theme


class _UpdateCheckWorker(QThread):
    finished_check = pyqtSignal(object)

    def run(self):
        self.finished_check.emit(check_for_update())


class SettingsDialog(QDialog):
    def __init__(self, current_theme_key, on_theme_change, parent=None):
        super().__init__(parent)
        self._on_theme_change = on_theme_change
        self._update_worker = None

        self.setWindowTitle("Réglages")
        self.setFixedWidth(340)
        self.setModal(True)
        self.setObjectName("settingsDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(14)

        title = QLabel("⚙ Réglages")
        title.setObjectName("settingsTitle")
        layout.addWidget(title)

        layout.addWidget(self._section_label("Thème"))

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("settingsThemeCombo")
        self.theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for key, label in theme.THEME_LABELS.items():
            self.theme_combo.addItem(label, key)
        current_idx = list(theme.THEME_LABELS.keys()).index(current_theme_key)
        self.theme_combo.setCurrentIndex(current_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        layout.addWidget(self.theme_combo)

        layout.addWidget(self._section_label("GitHub & mises à jour"))

        self.github_btn = self._action_button("🐙 Ouvrir le dépôt GitHub")
        self.github_btn.clicked.connect(self._open_github)
        self.github_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)
        layout.addWidget(self.github_btn)

        self.update_btn = self._action_button("🔄 Vérifier les mises à jour")
        self.update_btn.clicked.connect(self._check_updates)
        self.update_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)
        layout.addWidget(self.update_btn)

        if not config.GITHUB_UPDATES_ENABLED:
            note = QLabel(
                "Désactivés pour l'instant, le temps du développement — les mises à jour "
                "seront distribuées via le dépôt GitHub une fois celui-ci publié."
            )
            note.setWordWrap(True)
            note.setProperty("role", "faint")
            note.setObjectName("settingsNote")
            layout.addWidget(note)

        layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setObjectName("settingsCloseButton")
        close_btn.setProperty("variant", "dialog-close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

    def _section_label(self, text):
        label = QLabel(text)
        label.setObjectName("settingsSectionLabel")
        label.setProperty("role", "faint")
        return label

    def _action_button(self, text):
        btn = QPushButton(text)
        btn.setObjectName("settingsActionButton")
        btn.setProperty("variant", "settings-action")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(32)
        return btn

    def _on_theme_combo_changed(self, index):
        key = self.theme_combo.itemData(index)
        self._on_theme_change(key)

    def _open_github(self):
        QDesktopServices.openUrl(QUrl(config.GITHUB_URL))

    def _check_updates(self):
        self.update_btn.setEnabled(False)
        self.update_btn.setText("🔄 Vérification…")

        self._update_worker = _UpdateCheckWorker(self)
        self._update_worker.finished_check.connect(self._on_update_check_done)
        self._update_worker.start()

    def _on_update_check_done(self, result):
        self.update_btn.setText("🔄 Vérifier les mises à jour")
        self.update_btn.setEnabled(config.GITHUB_UPDATES_ENABLED)

        if not result.ok:
            QMessageBox.warning(
                self,
                "Vérification impossible",
                f"Impossible de vérifier les mises à jour : {result.error}",
            )
            return

        if result.update_available:
            QMessageBox.information(
                self,
                "Mise à jour disponible",
                f"Une nouvelle version est disponible : {result.latest_version} "
                f"(version actuelle : {result.current_version}).\n\n"
                "Ouvre le dépôt GitHub pour la télécharger.",
            )
        else:
            QMessageBox.information(
                self,
                "À jour",
                f"Tu utilises déjà la dernière version ({result.current_version}).",
            )