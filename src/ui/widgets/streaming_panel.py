from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from src import config
from src.core.models import DeviceType
from src.core.streaming import MONITOR_MIX_ID, STREAM_MIX_ID, STREAM_SINK_DESC
from src.ui import theme


CHANNEL_ICONS = {
    "game": "🎮",
    "chat": "💬",
    "media": "🎵",
    "music": "🎶",
    "mic_aux": "🎙️",
}


def _make_slider(accent):
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setStyleSheet(f"""
    QSlider::groove:horizontal {{ height: 4px; background: {theme.PANEL_ALT}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px; margin: -5px 0;
        border-radius: 7px; background: {accent};
    }}
    QSlider::handle:horizontal:hover {{
        width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
    }}
    """)
    return slider


class MixRow(QWidget):
    def __init__(self, label_text, accent, on_volume_change, on_mute_toggle):
        super().__init__()
        self._on_volume_change = on_volume_change
        self._on_mute_toggle = on_mute_toggle
        self._muted = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setFixedWidth(66)
        label.setStyleSheet(f"color: {theme.TEXT_DIM}; font-size: 10px; font-weight: 600;")
        layout.addWidget(label)

        self.slider = _make_slider(accent)
        self.slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self.slider, 1)

        self.value_label = QLabel("100%")
        self.value_label.setFixedWidth(40)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet(f"""
        background: {theme.PANEL_ALT};
        color: {accent};
        font-family: {theme.FONT_MONO};
        font-size: 10px;
        font-weight: 600;
        border-radius: 5px;
        padding: 3px 5px;
        """)
        layout.addWidget(self.value_label)

        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setFixedSize(26, 22)
        self.mute_btn.clicked.connect(self._toggle_mute)
        layout.addWidget(self.mute_btn)

        self._style_mute_btn()

    def _on_slider_change(self, value):
        self.value_label.setText(f"{value}%")
        self._on_volume_change(value / 100.0)

    def _toggle_mute(self):
        self._muted = not self._muted
        self._style_mute_btn()
        self._on_mute_toggle(self._muted)

    def _style_mute_btn(self):
        self.mute_btn.setText("🔇" if self._muted else "🔊")
        if self._muted:
            self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.DANGER_DIM};
                color: {theme.DANGER};
                border: 1px solid {theme.DANGER};
                border-radius: 6px;
                font-size: 11px;
            }}
            """)
        else:
            self.mute_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.TEXT_DIM};
                border: 1px solid {theme.BORDER};
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {theme.TEXT}; border-color: {theme.BORDER_STRONG}; }}
            """)

    def set_state(self, volume, mute, block_signals=True):
        if block_signals:
            self.slider.blockSignals(True)
        self.slider.setValue(int(volume * 100))
        if block_signals:
            self.slider.blockSignals(False)
        self.value_label.setText(f"{int(volume * 100)}%")
        self._muted = mute
        self._style_mute_btn()


class ChannelMixerCard(QFrame):
    def __init__(self, channel, mixer, sink_name_hint=""):
        super().__init__()
        self.channel = channel
        self.mixer = mixer
        self.setObjectName("channelMixerCard")
        self._apply_card_style(False)

        self._volume_timer = QTimer(self)
        self._volume_timer.setSingleShot(True)
        self._pending = {}
        self._volume_timer.timeout.connect(self._commit_pending)
        self._volume_safety_armed = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(8)

        head = QHBoxLayout()

        icon = QLabel(CHANNEL_ICONS.get(channel.id, "🔊"))
        icon.setFixedSize(20, 20)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 14px;")
        head.addWidget(icon, 0, Qt.AlignmentFlag.AlignVCenter)

        title = QLabel(channel.label)
        title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme.TEXT};")
        head.addWidget(title, 1)

        hint = QLabel(sink_name_hint)
        hint.setStyleSheet(f"color: {theme.TEXT_FAINT}; font-size: 9px; font-family: {theme.FONT_MONO};")
        head.addWidget(hint, 0, Qt.AlignmentFlag.AlignRight)
        outer.addLayout(head)

        self.monitor_row = MixRow(
            "🎧 Casque",
            theme.CYAN,
            lambda v: self._queue_volume(MONITOR_MIX_ID, v),
            lambda m: self._set_mute(MONITOR_MIX_ID, m),
        )
        outer.addWidget(self.monitor_row)

        self.stream_row = MixRow(
            "📡 Diffusion",
            theme.GREEN,
            lambda v: self._queue_volume(STREAM_MIX_ID, v),
            lambda m: self._set_mute(STREAM_MIX_ID, m),
        )
        outer.addWidget(self.stream_row)

        self.link_btn = QPushButton()
        self.link_btn.setCheckable(True)
        self.link_btn.setChecked(channel.linked)
        self.link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.link_btn.setFixedHeight(24)
        self.link_btn.clicked.connect(self._toggle_link)
        outer.addWidget(self.link_btn)

        self._style_link_btn()
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
        QFrame#channelMixerCard {{
            background: {bg};
            border: 1px solid {border};
            border-radius: 12px;
        }}
        """)

    def render_state(self):
        self.monitor_row.set_state(self.channel.monitor_volume, self.channel.monitor_mute)
        self.stream_row.set_state(self.channel.stream_volume, self.channel.stream_mute)
        self.link_btn.setChecked(self.channel.linked)
        self._style_link_btn()

        if self.channel.monitor_volume <= config.VOLUME_SAFETY_THRESHOLD:
            self._volume_safety_armed = True

    def _queue_volume(self, mix, volume):
        self._pending[mix] = volume
        self._volume_timer.start(100)
        if self.channel.linked:
            other_row = self.stream_row if mix == MONITOR_MIX_ID else self.monitor_row
            other_row.set_state(volume, other_row._muted)

    def _commit_pending(self):
        for mix, volume in dict(self._pending).items():
            affects_monitor = mix == MONITOR_MIX_ID or self.channel.linked
            is_increase_above_threshold = (
                affects_monitor
                and volume > config.VOLUME_SAFETY_THRESHOLD
                and volume > self.channel.monitor_volume
                and self._volume_safety_armed
            )

            if is_increase_above_threshold:
                if not self._confirm_high_volume(volume):
                    self._pending.pop(mix, None)
                    continue
                self._volume_safety_armed = False

            self.mixer.set_channel_volume(self.channel.id, mix, volume)

        self._pending.clear()
        self.monitor_row.set_state(self.channel.monitor_volume, self.channel.monitor_mute)
        self.stream_row.set_state(self.channel.stream_volume, self.channel.stream_mute)

    def _confirm_high_volume(self, target_volume: float) -> bool:
        threshold_pct = int(config.VOLUME_SAFETY_THRESHOLD * 100)
        answer = QMessageBox.warning(
            self,
            "Volume élevé",
            f"Tu es sur le point de monter le mix « 🎧 Casque » du canal "
            f"« {self.channel.label} » à {int(target_volume * 100)}%, au-dessus du "
            f"seuil de sécurité ({threshold_pct}%).\n\n"
            "Un volume trop élevé peut être dangereux pour ton audition. Confirmer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _set_mute(self, mix, muted):
        self.mixer.set_channel_mute(self.channel.id, mix, muted)

    def _toggle_link(self):
        self.mixer.set_channel_linked(self.channel.id, self.link_btn.isChecked())
        self.render_state()

    def _style_link_btn(self):
        linked = self.link_btn.isChecked()
        self.link_btn.setText("🔗 Curseurs liés" if linked else "✂️ Curseurs indépendants")
        accent = theme.CYAN if linked else theme.TEXT_FAINT
        self.link_btn.setStyleSheet(f"""
        QPushButton {{
            background: {theme.PANEL_ALT};
            color: {accent};
            border: 1px solid {theme.BORDER};
            border-radius: 7px;
            font-size: 10px;
        }}
        QPushButton:hover {{ border-color: {accent}; }}
        """)


class StreamingPanel(QWidget):
    def __init__(self, mixer, audio_manager, parent=None):
        super().__init__(parent)
        self.mixer = mixer
        self.audio = audio_manager
        self.cards = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)

        self.info_banner = QLabel()
        self.info_banner.setWordWrap(True)
        self.info_banner.setStyleSheet(f"""
        background: {theme.CYAN_DIM};
        color: {theme.TEXT};
        border: 1px solid {theme.CYAN};
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 11px;
        """)
        layout.addWidget(self.info_banner)

        toggle_row = QHBoxLayout()
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedHeight(34)
        self.toggle_btn.clicked.connect(self._on_toggle)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        layout.addWidget(self.cards_container)
        layout.addStretch()

        self._build_cards()
        self.render_state()

    def _build_cards(self):
        for channel in self.mixer.channels.values():
            card = ChannelMixerCard(channel, self.mixer, sink_name_hint=channel.sink_name)
            self.cards[channel.id] = card
            self.cards_layout.addWidget(card)

    def _default_output_device(self):
        for device in self.audio.get_devices(DeviceType.SINK):
            if device.is_default:
                return device
        return None

    def _on_toggle(self):
        device = self._default_output_device()
        already_muted = device.mute if device else True
        if device is not None and not already_muted:
            self.audio.set_mute(device, True)

        if self.mixer.is_enabled():
            self.mixer.disable()
        else:
            if not self.mixer.enable():
                self.info_banner.setText(
                    "Impossible d'activer le mode streaming : 'pactl' est introuvable "
                    "ou la création des périphériques virtuels a échoué."
                )

        self.render_state()

        if device is not None and not already_muted:
            QTimer.singleShot(
                config.STREAMING_TOGGLE_UNMUTE_DELAY_MS,
                lambda: self.audio.set_mute(device, False),
            )

    def render_state(self):
        enabled = self.mixer.is_enabled()

        self.toggle_btn.setText("⏹ Désactiver le mode streaming" if enabled else "▶ Activer le mode streaming")
        self.toggle_btn.setStyleSheet(f"""
        QPushButton {{
            background: {theme.DANGER_DIM if enabled else theme.CYAN_DIM};
            color: {theme.DANGER if enabled else theme.CYAN};
            border: 1px solid {theme.DANGER if enabled else theme.CYAN};
            border-radius: 8px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 700;
        }}
        """)

        if enabled:
            self.info_banner.setText(
                "Mode streaming actif. Dans OBS (ou équivalent), choisis "
                f"« Moniteur de {STREAM_SINK_DESC} » comme capture audio de bureau — "
                "c'est le mix « 📡 Diffusion » ci-dessous. Tu continues d'entendre le mix "
                "« 🎧 Casque » normalement. Déplace ensuite chaque application vers un "
                "canal depuis l'onglet Lecture."
            )
        else:
            self.info_banner.setText(
                "Le mode streaming crée des canaux virtuels (Jeu, Chat, Média, Micro/Aux) "
                "avec deux mixs indépendants — ce que tu entends (Casque) et ce que ton "
                "logiciel de streaming capture (Diffusion). Active-le pour commencer."
            )

        for card in self.cards.values():
            card.setEnabled(enabled)
            card.render_state()