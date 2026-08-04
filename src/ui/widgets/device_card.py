from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
)

from src import config
from src.core.models import is_headphone_device
from src.ui import theme
from src.ui.icons import Icons


class LedDot(QLabel):
    def __init__(self):
        super().__init__()
        self.setObjectName("deviceLed")
        self.setFixedSize(8, 8)
        self._color = None
        self.set_color(theme.GRAY_LED)

    def set_color(self, color: str):
        if color == self._color:
            return
        self._color = color
        self.setStyleSheet(f"background: {color}; border-radius: 4px;")


class DeviceCard(QFrame):
    def __init__(self, device, audio_manager, is_input=False, parent=None):
        super().__init__(parent)
        self.device = device
        self.audio = audio_manager
        self.is_input = is_input
        self.accent = theme.accent_for(is_input)
        self.accent_dim = theme.accent_dim_for(is_input)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(92)
        self.setObjectName("deviceCard")
        self._apply_card_style(False)

        self._pending_volume = device.volume
        self._volume_timer = QTimer(self)
        self._volume_timer.setSingleShot(True)
        self._volume_timer.timeout.connect(self._commit_volume)

        self._confirming_volume = False
        self._volume_safety_armed = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(8)

        # Icon: use qtawesome, no hardcoded emoji
        icon_name = "inputs" if is_input else "outputs"
        self.icon_label = QLabel()
        self.icon_label.setObjectName("deviceIcon")
        self.icon_label.setProperty("variant", "accent-cyan" if is_input else "accent-amber")
        self.icon_label.setFixedSize(22, 22)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = Icons.get(icon_name, color=self.accent)
        if icon:
            self.icon_label.setPixmap(icon.pixmap(16, 16))
        else:
            self.icon_label.setText("🎙️" if is_input else "🔊")
        self._apply_icon_style()
        top.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.led = LedDot()
        top.addWidget(self.led, 0, Qt.AlignmentFlag.AlignVCenter)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        self.title_label = QLabel()
        self.title_label.setObjectName("deviceTitle")
        title_box.addWidget(self.title_label)

        self.info_label = QLabel()
        self.info_label.setObjectName("deviceInfo")
        self.info_label.setProperty("role", "faint")
        title_box.addWidget(self.info_label)

        top.addLayout(title_box, 1)

        self.default_pill = QLabel("DEFAULT")
        self.default_pill.setObjectName("defaultPillInput" if is_input else "defaultPillOutput")
        top.addWidget(self.default_pill, 0, Qt.AlignmentFlag.AlignVCenter)

        outer.addLayout(top)

        volume_row = QHBoxLayout()
        volume_row.setSpacing(10)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("deviceVolumeSlider")
        self.volume_slider.setProperty("variant", "accent-cyan" if is_input else "accent-amber")
        self.volume_slider.setRange(0, 100)
        self._apply_slider_style()
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        volume_row.addWidget(self.volume_slider, 1)

        self.volume_value_label = QLabel()
        self.volume_value_label.setObjectName("valueBadgeCyan" if is_input else "valueBadgeAmber")
        self.volume_value_label.setFixedWidth(48)
        self.volume_value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        volume_row.addWidget(self.volume_value_label)

        outer.addLayout(volume_row)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.mute_btn = QPushButton()
        self.mute_btn.setObjectName("deviceMuteButton")
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setFixedHeight(26)
        self.mute_btn.clicked.connect(self.toggle_mute)
        actions.addWidget(self.mute_btn)

        self.default_btn = QPushButton("Définir par défaut")
        self.default_btn.setObjectName("deviceDefaultButton")
        self.default_btn.setProperty("variant", "ghost")
        self.default_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.default_btn.setFixedHeight(26)
        self.default_btn.clicked.connect(self.set_default)
        self._apply_default_button_style()
        actions.addWidget(self.default_btn)

        actions.addStretch()
        outer.addLayout(actions)

        self.render_state()

    def enterEvent(self, event):
        self._apply_card_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_card_style(False)
        super().leaveEvent(event)

    def _apply_card_style(self, hovered: bool):
        border = theme.BORDER if hovered else theme.BORDER_SOFT
        bg = theme.HOVER if hovered else theme.PANEL
        self.setStyleSheet(f"""
        QFrame#deviceCard {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}
        """)

    def _apply_icon_style(self):
        self.icon_label.setStyleSheet(
            f"color: {self.accent}; font-size: 15px; font-weight: 600;"
        )

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

    def _apply_default_button_style(self):
        self.default_btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {theme.TEXT_DIM};
            border: 1px solid {theme.BORDER};
            border-radius: 7px;
            padding: 4px 10px;
            font-size: 11px;
        }}
        QPushButton:hover {{
            color: {theme.TEXT};
            border-color: {self.accent};
        }}
        """)

    def update_state(self, device):
        self.device = device
        slider_busy = (
            self.volume_slider.isSliderDown()
            or self._volume_timer.isActive()
            or self._confirming_volume
        )

        external_change = (
            not self._confirming_volume
            and abs(device.volume - self._pending_volume) > 0.01
        )

        if slider_busy and external_change:
            self._volume_timer.stop()
            self._pending_volume = device.volume
            slider_busy = False

        if not slider_busy:
            self.render_state()
        else:
            self._render_text_only(use_pending_volume=True)

    def render_state(self):
        self.accent = theme.accent_for(self.is_input)
        self.accent_dim = theme.accent_dim_for(self.is_input)
        self._apply_icon_style()
        self._apply_slider_style()
        self._apply_default_button_style()

        self._render_text_only()
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(int(self.device.volume * 100))
        self.volume_slider.blockSignals(False)
        self._pending_volume = self.device.volume

        if self.device.volume <= config.VOLUME_SAFETY_THRESHOLD:
            self._volume_safety_armed = True

        if not self.audio.supports_per_device_volume():
            self.volume_slider.setEnabled(self.device.is_default)
        else:
            self.volume_slider.setEnabled(True)

    def _render_text_only(self, use_pending_volume=False):
        self.title_label.setText(self.device.description or self.device.name)
        self.info_label.setText(f"{self.device.name} • {self.device.state.value}")
        volume = self._pending_volume if use_pending_volume else self.device.volume
        self.volume_value_label.setText(f"{int(volume * 100)}%")
        self.default_pill.setVisible(self.device.is_default)
        self.led.set_color(theme.STATE_LED.get(self.device.state.value, theme.GRAY_LED))
        self._style_mute_btn()

    def _style_mute_btn(self):
        muted = self.device.mute
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
                border-radius: 7px;
                padding: 4px 10px;
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
                border-radius: 7px;
                padding: 4px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {theme.TEXT};
                border-color: {theme.BORDER_STRONG};
            }}
            """)

    def on_volume_change(self, value: int):
        self.volume_value_label.setText(f"{value}%")
        self._pending_volume = value / 100.0
        self._volume_timer.start(120)

    def _commit_volume(self):
        target = self._pending_volume

        is_increase_above_threshold = (
            not self.is_input
            and is_headphone_device(self.device)
            and target > config.VOLUME_SAFETY_THRESHOLD
            and target > self.device.volume
            and self._volume_safety_armed
        )

        if is_increase_above_threshold:
            self._confirming_volume = True
            confirmed = self._confirm_high_volume(target)
            self._confirming_volume = False
            if not confirmed:
                self._pending_volume = self.device.volume
                self.render_state()
                return
            self._volume_safety_armed = False

        if self.audio.set_volume(self.device, target):
            self._pending_volume = target
            self.volume_value_label.setText(f"{int(target * 100)}%")

    def _confirm_high_volume(self, target_volume: float) -> bool:
        threshold_pct = int(config.VOLUME_SAFETY_THRESHOLD * 100)
        answer = QMessageBox.warning(
            self,
            "Volume élevé",
            f"Tu es sur le point de monter « {self.device.description or self.device.name} » "
            f"à {int(target_volume * 100)}%, au-dessus du seuil de sécurité ({threshold_pct}%).\n\n"
            "Un volume trop élevé peut être dangereux pour ton audition. Confirmer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def toggle_mute(self):
        target = not self.device.mute
        if self.audio.set_mute(self.device, target):
            self.device.mute = target
            self._style_mute_btn()

    def set_default(self):
        self.audio.set_default_device(self.device)
