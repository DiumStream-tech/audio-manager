from src.ui import theme


def build_app_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background: {theme.BG};
        color: {theme.TEXT};
        font-family: {theme.FONT_UI};
        font-size: 13px;
    }}

    QLabel {{
        background: transparent;
        color: {theme.TEXT};
    }}

    QLabel[role="muted"] {{
        color: {theme.TEXT_DIM};
    }}

    QLabel[role="faint"] {{
        color: {theme.TEXT_FAINT};
    }}

    QLabel[role="danger"] {{
        color: {theme.DANGER};
    }}

    QPushButton {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER};
        border-radius: 8px;
        padding: 6px 12px;
    }}

    QPushButton:hover {{
        background: {theme.HOVER};
        border-color: {theme.BORDER_STRONG};
    }}

    QPushButton:pressed {{
        background: {theme.PANEL};
    }}

    QPushButton:disabled {{
        color: {theme.TEXT_FAINT};
        border-color: {theme.BORDER_SOFT};
        background: {theme.PANEL_ALT};
    }}

    QPushButton[variant="ghost"] {{
        background: transparent;
        color: {theme.TEXT_DIM};
    }}

    QPushButton[variant="ghost"]:hover {{
        color: {theme.TEXT};
        border-color: {theme.BORDER_STRONG};
        background: transparent;
    }}

    QPushButton[variant="danger"] {{
        background: {theme.DANGER_DIM};
        color: {theme.DANGER};
        border: 1px solid {theme.DANGER};
        font-weight: 600;
    }}

    QPushButton[variant="danger"]:hover {{
        background: {theme.DANGER_DIM};
        border-color: {theme.DANGER};
    }}

    QPushButton[variant="accent-cyan"] {{
        background: {theme.CYAN_DIM};
        color: {theme.CYAN};
        border: 1px solid {theme.CYAN};
        font-weight: 600;
    }}

    QPushButton[variant="accent-amber"] {{
        background: {theme.AMBER_DIM};
        color: {theme.AMBER};
        border: 1px solid {theme.AMBER};
        font-weight: 600;
    }}

    QPushButton[variant="accent-green"] {{
        background: {theme.PANEL_ALT};
        color: {theme.GREEN};
        border: 1px solid {theme.GREEN};
        font-weight: 600;
    }}

    QPushButton[variant="sidebar-action"] {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER};
        border-radius: 7px;
        padding: 6px 10px;
        font-size: 11px;
        margin: 4px 12px 8px 12px;
    }}

    QPushButton[variant="sidebar-action"]:hover {{
        background: {theme.HOVER};
        border-color: {theme.BORDER_STRONG};
        color: {theme.TEXT};
    }}

    QPushButton#sidebarRefreshButton[variant="sidebar-action"] {{
        margin: 4px 12px 12px 12px;
    }}

    QPushButton[variant="settings-action"] {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER};
        border-radius: 7px;
        padding: 4px 10px;
        font-size: 12px;
        text-align: left;
    }}

    QPushButton[variant="settings-action"]:hover:!disabled {{
        background: {theme.HOVER};
        border-color: {theme.BORDER_STRONG};
    }}

    QPushButton[variant="settings-action"]:disabled {{
        color: {theme.TEXT_FAINT};
        border-color: {theme.BORDER_SOFT};
        background: {theme.PANEL_ALT};
    }}

    QPushButton[variant="dialog-close"] {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER};
        border-radius: 7px;
        padding: 7px 16px;
        font-size: 12px;
    }}

    QPushButton[variant="dialog-close"]:hover {{
        border-color: {theme.BORDER_STRONG};
        background: {theme.HOVER};
    }}

    QPushButton#navButton {{
        text-align: left;
        border: none;
        border-radius: 0;
        border-left: 3px solid transparent;
        background: transparent;
        color: {theme.TEXT_DIM};
        font-size: 12px;
        padding-left: 10px;
    }}

    QPushButton#navButton:hover {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
    }}

    QPushButton#navButton:checked {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        font-weight: 600;
    }}

    QPushButton#navButton[variant="nav-cyan"]:checked {{
        border-left: 3px solid {theme.CYAN};
    }}

    QPushButton#navButton[variant="nav-amber"]:checked {{
        border-left: 3px solid {theme.AMBER};
    }}

    QPushButton#navButton[variant="nav-green"]:checked {{
        border-left: 3px solid {theme.GREEN};
    }}

    QComboBox {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER};
        border-radius: 8px;
        padding: 6px 10px;
    }}

    QComboBox:hover {{
        border-color: {theme.BORDER_STRONG};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 18px;
    }}

    QComboBox QAbstractItemView {{
        background: {theme.PANEL};
        color: {theme.TEXT};
        border: 1px solid {theme.BORDER_STRONG};
        selection-background-color: {theme.HOVER};
        selection-color: {theme.TEXT};
        outline: none;
    }}

    QComboBox#settingsThemeCombo {{
        border-radius: 7px;
        font-size: 12px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {theme.BORDER};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {theme.BORDER_STRONG};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QFrame#sidebar {{
        background: {theme.PANEL};
        border-right: 1px solid {theme.BORDER_SOFT};
    }}

    QWidget#mainContent {{
        background: {theme.BG};
    }}

    QFrame#deviceCard {{
        background: {theme.PANEL};
        border: 1px solid {theme.BORDER_SOFT};
        border-radius: 12px;
    }}

    QFrame#streamCard {{
        background: {theme.PANEL};
        border: 1px solid {theme.BORDER_SOFT};
        border-radius: 10px;
    }}

    QFrame#channelMixerCard {{
        background: {theme.PANEL};
        border: 1px solid {theme.BORDER_SOFT};
        border-radius: 12px;
    }}

    QDialog#settingsDialog {{
        background: {theme.PANEL};
        color: {theme.TEXT};
    }}

    QLabel#settingsTitle {{
        font-size: 15px;
        font-weight: 700;
        color: {theme.TEXT};
    }}

    QLabel#settingsSectionLabel {{
        color: {theme.TEXT_FAINT};
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1px;
    }}

    QLabel#settingsNote {{
        color: {theme.TEXT_FAINT};
        font-size: 10px;
    }}

    QLabel#mainHeaderTitle {{
        font-size: 20px;
        font-weight: 700;
        color: {theme.TEXT};
    }}

    QLabel#mainHeaderSubtitle {{
        font-size: 11px;
        color: {theme.TEXT_FAINT};
        font-family: {theme.FONT_MONO};
    }}

    QLabel#sidebarTitle {{
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
        color: {theme.TEXT};
    }}

    QLabel#sidebarVersion {{
        font-size: 10px;
        color: {theme.TEXT_FAINT};
        font-family: {theme.FONT_MONO};
    }}

    QFrame#sidebarSeparator {{
        background: {theme.BORDER_SOFT};
        border: none;
    }}

    QLabel#warningBanner {{
        background: {theme.DANGER_DIM};
        color: {theme.DANGER};
        border: 1px solid {theme.DANGER};
        border-radius: 10px;
        padding: 9px 12px;
        font-size: 12px;
    }}

    QLabel#infoBanner {{
        background: {theme.CYAN_DIM};
        color: {theme.TEXT};
        border: 1px solid {theme.CYAN};
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 11px;
    }}

    QLabel#statusPill {{
        background: {theme.PANEL_ALT};
        color: {theme.TEXT_FAINT};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 9px;
        padding: 3px 9px;
    }}

    QLabel#valueBadgeCyan {{
        background: {theme.PANEL_ALT};
        color: {theme.CYAN};
        font-family: {theme.FONT_MONO};
        font-weight: 600;
        border-radius: 6px;
        padding: 3px 6px;
    }}

    QLabel#valueBadgeAmber {{
        background: {theme.PANEL_ALT};
        color: {theme.AMBER};
        font-family: {theme.FONT_MONO};
        font-weight: 600;
        border-radius: 6px;
        padding: 3px 6px;
    }}

    QLabel#valueBadgeGreen {{
        background: {theme.PANEL_ALT};
        color: {theme.GREEN};
        font-family: {theme.FONT_MONO};
        font-weight: 600;
        border-radius: 6px;
        padding: 3px 6px;
    }}

    QLabel#defaultPillInput {{
        background: {theme.CYAN_DIM};
        color: {theme.CYAN};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 8px;
        padding: 2px 8px;
    }}

    QLabel#defaultPillOutput {{
        background: {theme.AMBER_DIM};
        color: {theme.AMBER};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
        border-radius: 8px;
        padding: 2px 8px;
    }}

    QLabel#listPlaceholder {{
        color: {theme.TEXT_FAINT};
        padding: 24px 4px;
        font-size: 12px;
    }}

    QStatusBar {{
        background: {theme.BG};
        color: {theme.TEXT_FAINT};
        border-top: 1px solid {theme.BORDER_SOFT};
    }}
    """