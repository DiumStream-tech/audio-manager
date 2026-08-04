"""Changelog dialog — shows per-version changes with a 'NEW' badge on the latest."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src import config, i18n
from src.core.changelog import VERSION_ORDER, get_changes, has_changes
from src.ui.icons import Icons


class ChangelogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("changelog.title"))
        self.setFixedWidth(480)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setObjectName("changelogDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("changelogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 14)
        header_layout.setSpacing(10)

        icon_lbl = QLabel()
        changelog_icon = Icons.get("changelog")
        if changelog_icon:
            icon_lbl.setPixmap(changelog_icon.pixmap(20, 20))
            header_layout.addWidget(icon_lbl)

        title_lbl = QLabel(i18n.t("changelog.title"))
        title_lbl.setObjectName("changelogTitle")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        version_lbl = QLabel(f"v{config.APP_VERSION}")
        version_lbl.setObjectName("changelogVersionBadge")
        header_layout.addWidget(version_lbl)

        root.addWidget(header)

        sep = QFrame()
        sep.setObjectName("changelogSep")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # ── Scrollable content ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("changelogContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(20)

        lang = i18n.get_language()
        latest_version = config.APP_VERSION

        # Render versions newest → oldest
        for version in reversed(VERSION_ORDER):
            block = self._build_version_block(version, lang, is_latest=(version == latest_version))
            content_layout.addWidget(block)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        sep2 = QFrame()
        sep2.setObjectName("changelogSep")
        sep2.setFixedHeight(1)
        root.addWidget(sep2)

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("changelogFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 14)

        footer_layout.addStretch()
        close_btn = QPushButton(i18n.t("changelog.close"))
        close_btn.setObjectName("changelogCloseButton")
        close_btn.setProperty("variant", "dialog-close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        Icons.apply_to_button(close_btn, "close", i18n.t("changelog.close"))
        footer_layout.addWidget(close_btn)

        root.addWidget(footer)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_version_block(self, version: str, lang: str, is_latest: bool) -> QWidget:
        block = QWidget()
        block.setObjectName("changelogBlock")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Version row
        row = QHBoxLayout()
        row.setSpacing(8)

        ver_lbl = QLabel(f"v{version}")
        ver_lbl.setObjectName("changelogBlockVersion")
        row.addWidget(ver_lbl)

        if is_latest:
            badge = QLabel(i18n.t("changelog.new_badge"))
            badge.setObjectName("changelogNewBadge")
            row.addWidget(badge)

        row.addStretch()
        layout.addLayout(row)

        # Separator line
        line = QFrame()
        line.setObjectName("changelogBlockLine")
        line.setFixedHeight(1)
        layout.addWidget(line)

        # Changes list
        changes = get_changes(version, lang)

        if changes is None:
            note = QLabel(i18n.t("changelog.unavailable"))
            note.setObjectName("changelogNoInfo")
            note.setProperty("role", "faint")
            note.setWordWrap(True)
            layout.addWidget(note)
        elif len(changes) == 0:
            note = QLabel(i18n.t("changelog.unknown"))
            note.setObjectName("changelogNoInfo")
            note.setProperty("role", "faint")
            note.setWordWrap(True)
            layout.addWidget(note)
        else:
            for change in changes:
                item_row = QHBoxLayout()
                item_row.setSpacing(8)
                item_row.setContentsMargins(4, 0, 0, 0)

                bullet = QLabel("•")
                bullet.setObjectName("changelogBullet")
                bullet.setFixedWidth(12)
                item_row.addWidget(bullet, 0, Qt.AlignmentFlag.AlignTop)

                text = QLabel(change)
                text.setObjectName("changelogItem")
                text.setWordWrap(True)
                item_row.addWidget(text, 1)

                layout.addLayout(item_row)

        return block
