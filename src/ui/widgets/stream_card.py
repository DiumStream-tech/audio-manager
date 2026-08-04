from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
)

from src.core.settings import get_settings_store
from src.ui import theme
from src.ui.icon_loader import fetch_icon
from src.ui.icons import Icons


class StreamCard(QFrame):
    def __init__(self, stream, audio_manager, target_devices, is_input=False,
                 streaming_enabled=False, parent=None):
        super().__init__(parent)
        self.stream = stream
        self.audio = audio_manager
        self.target_devices = target_devices
        self.is_input = is_input
        self.streaming_enabled = streaming_enabled
        self.accent = theme.accent_for(is_input)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(112)
        self.setObjectName("streamCard")
        self._apply_card_style(False)

        self._pending_volume = stream.volume
        self._volume_timer = QTimer(self)
        self._volume_timer.setSingleShot(True)
        self._volume_timer.timeout.connect(self._commit_volume)

        self._last_icon_url = None
        self._last_fallback_char = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(10)

        head = QHBoxLayout()

        self.icon_label = QLabel()
        self.icon_label.setObjectName("streamIcon")
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.title_label = QLabel()
        self.title_label.setObjectName("streamTitle")
        title_box.addWidget(self.title_label)

        self.info_label = QLabel()
        self.info_label.setObjectName("streamInfo")
        self.info_label.setProperty("role", "faint")
        title_box.addWidget(self.info_label)
        head.addLayout(title_box, 1)

        self.status_pill = QLabel("EN ATTENTE")
        self.status_pill.setObjectName("statusPill")
        head.addWidget(self.status_pill, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(head)

        vol = QHBoxLayout()
        vol.setSpacing(12)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("streamVolumeSlider")
        self.volume_slider.setProperty("variant", "accent-cyan" if is_input else "accent-amber")
        self.volume_slider.setRange(0, 100)
        self._apply_slider_style()
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        vol.addWidget(self.volume_slider, 1)

        self.volume_value_label = QLabel()
        self.volume_value_label.setObjectName("valueBadgeCyan" if is_input else "valueBadgeAmber")
        self.volume_value_label.setFixedWidth(52)
        self.volume_value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        vol.addWidget(self.volume_value_label)
        outer.addLayout(vol)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        self.mute_btn = QPushButton()
        self.mute_btn.setObjectName("streamMuteButton")
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setFixedHeight(28)
        self.mute_btn.clicked.connect(self.toggle_mute)
        ctrl.addWidget(self.mute_btn)

        self.device_labels = []
        self.device_map = {}
        self._set_target_devices(target_devices)

        self.device_select = QComboBox()
        self.device_select.setObjectName("streamDeviceSelect")
        self.device_select.addItems(self.device_labels or ["Aucun périphérique"])
        self.device_select.setEnabled(bool(self.device_map))
        self.device_select.activated.connect(self._on_device_selected)
        ctrl.addWidget(self.device_select, 1)

        outer.addLayout(ctrl)
        self.render_state()

    # ── hover ──────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._apply_card_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_card_style(False)
        super().leaveEvent(event)

    # ── styles ─────────────────────────────────────────────────────────────

    def _apply_card_style(self, hovered: bool):
        border = theme.BORDER if hovered else theme.BORDER_SOFT
        bg = theme.HOVER if hovered else theme.PANEL
        self.setStyleSheet(f"""
        QFrame#streamCard {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 10px;
        }}
        """)

    def _apply_slider_style(self):
        self.volume_slider.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            height: 4px;
            background: {theme.PANEL_ALT};
            border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: {self.accent};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 7px;
            background: {self.accent};
        }}
        QSlider::handle:horizontal:hover {{
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        """)

    def _apply_muted_style(self, muted: bool):
        mute_icon = Icons.get("volume_mute", color=theme.DANGER) if muted else Icons.get("volume_up", color=theme.TEXT_DIM)
        mute_text = "Réactiver" if muted else "Muet"
        if mute_icon:
            self.mute_btn.setIcon(mute_icon)
            self.mute_btn.setText(f" {mute_text}")
        else:
            self.mute_btn.setText(("🔇 " if muted else "🔊 ") + mute_text)

        if muted:
            self.mute_btn.setProperty("variant", "danger")
            self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.DANGER_DIM};
                color: {theme.DANGER};
                border: 1px solid {theme.DANGER};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme.DANGER_DIM};
                border-color: {theme.DANGER};
            }}
            """)
        else:
            self.mute_btn.setProperty("variant", "ghost")
            self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.TEXT_DIM};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {theme.TEXT};
                border-color: {theme.BORDER_STRONG};
            }}
            """)

    # ── device list ────────────────────────────────────────────────────────

    def _set_target_devices(self, target_devices):
        self.target_devices = target_devices
        self.device_labels = []
        self.device_map = {}
        for d in target_devices:
            label = d.description or d.name
            self.device_labels.append(label)
            self.device_map[label] = d

    def update_target_devices(self, target_devices):
        new_indexes = {getattr(d, "index", None) for d in target_devices}
        current_indexes = {getattr(d, "index", None) for d in self.target_devices}

        # Bug fix: always rebuild the label map even when index sets match,
        # so description changes (e.g. after a rename) are reflected.
        previously_selected_device = self.device_map.get(self.device_select.currentText())
        self._set_target_devices(target_devices)

        if new_indexes == current_indexes:
            return

        self.device_select.blockSignals(True)
        self.device_select.clear()
        self.device_select.addItems(self.device_labels or ["Aucun périphérique"])
        self.device_select.setEnabled(bool(self.device_map))
        self.device_select.blockSignals(False)

        if previously_selected_device is not None:
            for label, device in self.device_map.items():
                if getattr(device, "index", None) == getattr(previously_selected_device, "index", None):
                    idx = self.device_select.findText(label)
                    if idx >= 0:
                        self.device_select.blockSignals(True)
                        self.device_select.setCurrentIndex(idx)
                        self.device_select.blockSignals(False)
                    break

    # ── state ──────────────────────────────────────────────────────────────

    def update_state(self, stream, target_devices=None, streaming_enabled=None):
        self.stream = stream
        if streaming_enabled is not None:
            self.streaming_enabled = streaming_enabled
        if target_devices is not None:
            self.update_target_devices(target_devices)

        slider_busy = self.volume_slider.isSliderDown() or self._volume_timer.isActive()
        external_change = abs(stream.volume - self._pending_volume) > 0.01

        if slider_busy and external_change:
            self._volume_timer.stop()
            self._pending_volume = stream.volume
            slider_busy = False

        if not slider_busy:
            self.render_state()
        else:
            self._render_text_only(use_pending_volume=True)
        self._sync_device_selection()

    def render_state(self):
        self.accent = theme.accent_for(self.is_input)
        self._apply_slider_style()
        self._render_text_only()

        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(int(self.stream.volume * 100))
        self.volume_slider.blockSignals(False)
        self._pending_volume = self.stream.volume

        is_placeholder = getattr(self.stream, "is_placeholder", False)
        self.volume_slider.setEnabled(not is_placeholder)
        self.mute_btn.setEnabled(not is_placeholder)
        self.device_select.setEnabled(not is_placeholder and bool(self.device_map))

        self._sync_device_selection()

    def _sync_device_selection(self):
        if not self.device_map:
            return

        selected_label = None

        for label, device in self.device_map.items():
            if getattr(device, "index", None) == getattr(self.stream, "device_index", None):
                selected_label = label
                break

        if selected_label is None:
            for label, device in self.device_map.items():
                if getattr(device, "is_default", False):
                    selected_label = label
                    break

        if selected_label is None:
            return

        idx = self.device_select.findText(selected_label)
        if idx >= 0 and idx != self.device_select.currentIndex():
            self.device_select.blockSignals(True)
            self.device_select.setCurrentIndex(idx)
            self.device_select.blockSignals(False)

    # ── icons (application icons from the web) ────────────────────────────

    def _set_icon_from_url(self, url: str, fallback_char: str):
        self._show_fallback_icon(fallback_char)
        fetch_icon(url, lambda data: self._on_icon_fetched(data, fallback_char))

    def _on_icon_fetched(self, data, fallback_char):
        try:
            self._render_icon_bytes(data, fallback_char)
        except RuntimeError:
            pass

    def _render_icon_bytes(self, data, fallback_char):
        if not data:
            self._show_fallback_icon(fallback_char)
            return
        try:
            renderer = QSvgRenderer(data)
            if not renderer.isValid():
                raise ValueError("invalid svg")
            pixmap = QPixmap(18, 18)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setText("")
            self.icon_label.setStyleSheet("")
        except Exception:
            self._show_fallback_icon(fallback_char)

    def _show_fallback_icon(self, fallback_char: str):
        self.icon_label.setPixmap(QPixmap())
        self.icon_label.setText(fallback_char)
        self.icon_label.setStyleSheet(
            f"color: {self.accent}; font-size: 14px; font-weight: 700;"
        )

    # ── text rendering ─────────────────────────────────────────────────────

    def _render_text_only(self, use_pending_volume=False):
        name = self.stream.application_name or self.stream.name or f"Stream #{self.stream.index}"
        icon_url = getattr(self.stream, "application_icon_url", "") or ""
        fallback_char = (name[:1] if name else "?").upper()

        if icon_url != self._last_icon_url or fallback_char != self._last_fallback_char:
            self._last_icon_url = icon_url
            self._last_fallback_char = fallback_char
            self._set_icon_from_url(icon_url, fallback_char)
        elif self.icon_label.pixmap() is None or self.icon_label.pixmap().isNull():
            self._show_fallback_icon(fallback_char)

        self.title_label.setText(name)

        is_placeholder = getattr(self.stream, "is_placeholder", False)
        if is_placeholder:
            self.info_label.setText("application lancée · pas de son actif")
            self.status_pill.setText("EN ATTENTE")
            self.status_pill.setVisible(True)
        else:
            self.info_label.setText(f"stream #{self.stream.index}")
            self.status_pill.setVisible(False)

        volume = self._pending_volume if use_pending_volume else self.stream.volume
        self.volume_value_label.setText(f"{int(volume * 100)}%")
        self._apply_muted_style(self.stream.mute)

    # ── volume / mute ──────────────────────────────────────────────────────

    def on_volume_change(self, value: int):
        self.volume_value_label.setText(f"{value}%")
        self._pending_volume = value / 100.0
        self._volume_timer.start(120)

    def _commit_volume(self):
        if self.audio.set_stream_volume(self.stream, self._pending_volume):
            self.volume_value_label.setText(f"{int(self._pending_volume * 100)}%")

    def toggle_mute(self):
        new_mute = not self.stream.mute
        if self.audio.set_stream_mute(self.stream, new_mute):
            self.stream.mute = new_mute
            self._apply_muted_style(new_mute)

    def _on_device_selected(self, index: int):
        selected = self.device_select.itemText(index)
        device = self.device_map.get(selected)
        if device and self.audio.move_stream(self.stream, device):
            app_name = getattr(self.stream, "application_name", "") or ""
            if app_name:
                kind = "recording" if self.is_input else "playback"
                get_settings_store().set_stream_route(
                    kind,
                    app_name,
                    device.name,
                    self.streaming_enabled,
                )
