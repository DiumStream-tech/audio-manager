"""Polished update-result dialog replacing the plain QMessageBox."""

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src import config, i18n
from src.ui.icons import Icons


class UpdateResultDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        icon_type: str = "info",   # "info" | "warning" | "success"
        show_github_btn: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(400)
        self.setModal(True)
        self.setObjectName("updateResultDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName(f"updateResultHeader_{icon_type}")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 14)
        header_layout.setSpacing(10)

        icon_map = {
            "info": "check_updates",
            "warning": "warning",
            "success": "check_updates",
        }
        icon_name = icon_map.get(icon_type, "check_updates")
        icon_lbl = QLabel()
        icon = Icons.get(icon_name)
        if icon:
            icon_lbl.setPixmap(icon.pixmap(22, 22))
            header_layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("updateResultTitle")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        root.addWidget(header)

        sep = QFrame()
        sep.setObjectName("updateResultSep")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── Body ────────────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("updateResultBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(10)

        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("updateResultMessage")
        msg_lbl.setWordWrap(True)
        body_layout.addWidget(msg_lbl)

        root.addWidget(body)

        sep2 = QFrame()
        sep2.setObjectName("updateResultSep")
        sep2.setFixedHeight(1)
        root.addWidget(sep2)

        # ── Footer ──────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("updateResultFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 14)
        footer_layout.setSpacing(8)

        footer_layout.addStretch()

        if show_github_btn:
            github_btn = QPushButton()
            github_btn.setObjectName("updateResultGithubBtn")
            github_btn.setProperty("variant", "settings-action")
            github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            github_btn.setFixedHeight(32)
            Icons.apply_to_button(github_btn, "github", i18n.t("settings.open_github"))
            github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(config.GITHUB_URL)))
            footer_layout.addWidget(github_btn)

        close_btn = QPushButton(i18n.t("settings.close"))
        close_btn.setObjectName("updateResultCloseBtn")
        close_btn.setProperty("variant", "dialog-close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        Icons.apply_to_button(close_btn, "close", i18n.t("settings.close"))
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        root.addWidget(footer)
