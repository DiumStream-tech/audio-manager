from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src import config
from src.core.manager import get_audio_manager
from src.core.models import DeviceType
from src.core.settings import get_settings_store
from src.core.streaming import get_streaming_mixer
from src.ui import theme
from src.ui.app_style import build_app_stylesheet
from src.ui.widgets.device_card import DeviceCard
from src.ui.widgets.settings_dialog import SettingsDialog
from src.ui.widgets.stream_card import StreamCard
from src.ui.widgets.streaming_panel import StreamingPanel


NAV_SECTIONS = [
    ("outputs", "Sorties", "▶", False),
    ("inputs", "Entrées", "◀", True),
    ("playback", "Lecture", "♪", False),
    ("recording", "Enregistrement", "●", True),
    ("streaming", "Streaming", "📡", None),
]


class NavButton(QPushButton):
    def __init__(self, glyph, label, accent_variant):
        super().__init__()
        self.setCheckable(True)
        self.setText(f" {glyph} {label}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setObjectName("navButton")
        self.setProperty("variant", accent_variant)


class MainWindow(QMainWindow):
    _audio_changed_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._settings = get_settings_store()
        self.audio = get_audio_manager()
        self.streams_supported = self.audio.supports_streams()
        self.streaming_mixer = get_streaming_mixer()
        self.streaming_supported = self.streaming_mixer.is_available()
        self._pages = {}
        self._nav_buttons = {}
        self._refresh_scheduled = False
        self._routed_stream_indices = {}
        self._last_streaming_enabled = False

        self.setWindowTitle(f"{config.APP_NAME} — {self.audio.backend_name}")
        self.resize(*config.WINDOW_DEFAULT_SIZE)
        self.setMinimumSize(*config.WINDOW_MIN_SIZE)

        self._audio_changed_signal.connect(self.refresh_ui)
        self.audio.add_callback(self.on_audio_changed)
        self.audio.start_monitoring(interval=config.MONITOR_INTERVAL_SECONDS)

        self._setup_ui()
        self.refresh_ui()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("mainCentral")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        content = QWidget()
        content.setObjectName("mainContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 12)
        content_layout.setSpacing(10)

        self.header_title = QLabel("Gestionnaire audio")
        self.header_title.setObjectName("mainHeaderTitle")
        content_layout.addWidget(self.header_title)

        self.header_subtitle = QLabel(self.audio.backend_name)
        self.header_subtitle.setObjectName("mainHeaderSubtitle")
        self.header_subtitle.setProperty("role", "faint")
        content_layout.addWidget(self.header_subtitle)

        self.warning_banner = QLabel()
        self.warning_banner.setObjectName("warningBanner")
        self.warning_banner.setWordWrap(True)
        self.warning_banner.hide()
        content_layout.addWidget(self.warning_banner)

        self.stack = QStackedWidget()
        self.stack.setObjectName("mainStack")
        content_layout.addWidget(self.stack, 1)

        root.addWidget(content, 1)

        for key, label, glyph, is_input in NAV_SECTIONS:
            if key in ("playback", "recording") and not self.streams_supported:
                continue
            if key == "streaming" and not self.streaming_supported:
                continue
            page = self._build_streaming_page() if key == "streaming" else self._build_scroll_page()
            self._pages[key] = page
            self.stack.addWidget(page)

        missing = self.audio.missing_requirements()
        if missing:
            self.warning_banner.setText(
                f"{self.audio.backend_name} : certaines fonctions sont indisponibles.\n" + "\n".join(missing)
            )
            self.warning_banner.show()

        initial_key = self._settings.get_last_section()
        if initial_key not in self._nav_buttons:
            initial_key = "outputs"
        if initial_key in self._nav_buttons:
            self._nav_buttons[initial_key].setChecked(True)
            self._show_section(initial_key)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(188)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        brand = QWidget()
        brand.setObjectName("sidebarBrand")
        brand.setFixedHeight(76)

        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 16, 16, 8)
        brand_layout.setSpacing(2)

        title = QLabel("AUDIO MANAGER")
        title.setObjectName("sidebarTitle")
        brand_layout.addWidget(title)

        version = QLabel(f"v{config.APP_VERSION}")
        version.setObjectName("sidebarVersion")
        version.setProperty("role", "faint")
        brand_layout.addWidget(version)

        layout.addWidget(brand)

        sep = QFrame()
        sep.setObjectName("sidebarSeparator")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(8)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        for key, label, glyph, is_input in NAV_SECTIONS:
            if key in ("playback", "recording") and not self.streams_supported:
                continue
            if key == "streaming" and not self.streaming_supported:
                continue

            accent_variant = "nav-green" if is_input is None else ("nav-cyan" if is_input else "nav-amber")
            button = NavButton(glyph, label, accent_variant)
            button.clicked.connect(lambda _checked=False, k=key: self._show_section(k))
            self._nav_group.addButton(button)
            layout.addWidget(button)
            self._nav_buttons[key] = button

        layout.addStretch()

        settings_btn = QPushButton("⚙ Réglages")
        settings_btn.setObjectName("sidebarSettingsButton")
        settings_btn.setProperty("variant", "sidebar-action")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        refresh_btn = QPushButton("↻ Actualiser")
        refresh_btn.setObjectName("sidebarRefreshButton")
        refresh_btn.setProperty("variant", "sidebar-action")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_ui)
        layout.addWidget(refresh_btn)

        return sidebar

    def _build_scroll_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setObjectName("scrollPage")
        inner = QVBoxLayout(container)
        inner.setContentsMargins(2, 2, 2, 2)
        inner.setSpacing(8)
        inner.addStretch()

        scroll.setWidget(container)
        scroll.cards = {}
        scroll.placeholder = None
        return scroll

    def _build_streaming_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        panel = StreamingPanel(self.streaming_mixer, self.audio)
        scroll.setWidget(panel)
        scroll.cards = {}
        scroll.placeholder = None
        return scroll

    def _show_section(self, key):
        if key in self._pages:
            self.stack.setCurrentWidget(self._pages[key])
            self._settings.set_last_section(key)

    def _fill_devices(self, key, dtype, is_input):
        tab = self._pages[key]
        devices = self.audio.get_devices(dtype)

        if is_input:
            devices = [device for device in devices if not device.name.endswith(".monitor")]

        if not is_input:
            channel_sink_names = {c.sink_name for c in self.streaming_mixer.channels.values()}
            devices = [device for device in devices if device.name not in channel_sink_names]

        self._sync_list(
            tab=tab,
            items=devices,
            key=lambda device: device.index,
            make=lambda device: DeviceCard(device, self.audio, is_input=is_input),
            update=lambda card, device: card.update_state(device),
            empty_text="Aucun périphérique détecté.",
        )

    def _fill_streams(self, key, stype, target_dtype):
        tab = self._pages[key]
        streams = self.audio.get_streams(stype)

        internal_indices = self.streaming_mixer.internal_stream_indices(stype)
        if internal_indices:
            streams = [s for s in streams if s.index not in internal_indices]

        devices = [
            device
            for device in self.audio.get_devices(target_dtype)
            if not device.name.endswith(".monitor")
        ]

        is_input = target_dtype == DeviceType.SOURCE
        streaming_enabled = self.streaming_mixer.is_enabled()

        self._apply_saved_routes(stype, streams, devices, is_input, streaming_enabled)

        self._sync_list(
            tab=tab,
            items=streams,
            key=lambda stream: stream.index,
            make=lambda stream: StreamCard(
                stream,
                self.audio,
                devices,
                is_input=is_input,
                streaming_enabled=streaming_enabled,
            ),
            update=lambda card, stream: card.update_state(stream, devices, streaming_enabled),
            empty_text="Aucune application audio détectée.",
        )

    def _apply_saved_routes(self, stype, streams, devices, is_input, streaming_enabled):
        already_routed = self._routed_stream_indices.setdefault(stype, set())
        kind = "recording" if is_input else "playback"
        devices_by_name = {device.name: device for device in devices}

        current_indices = {stream.index for stream in streams}
        already_routed.intersection_update(current_indices)

        for stream in streams:
            if stream.index in already_routed:
                continue
            already_routed.add(stream.index)

            app_name = getattr(stream, "application_name", "") or ""
            if not app_name:
                continue

            saved_device_name = self._settings.get_stream_route(kind, app_name, streaming_enabled)
            if not saved_device_name:
                continue

            target_device = devices_by_name.get(saved_device_name)
            if target_device is None or target_device.index == stream.device_index:
                continue

            self.audio.move_stream(stream, target_device)

    def _sync_list(self, tab, items, key, make, update, empty_text):
        layout = tab.widget().layout()
        seen = set()

        for pos, item in enumerate(items):
            item_key = key(item)
            seen.add(item_key)

            if item_key in tab.cards:
                card = tab.cards[item_key]
                update(card, item)
                if layout.indexOf(card) != pos:
                    layout.removeWidget(card)
                    layout.insertWidget(pos, card)
            else:
                card = make(item)
                layout.insertWidget(pos, card)
                tab.cards[item_key] = card

        for item_key in list(tab.cards.keys()):
            if item_key not in seen:
                widget = tab.cards.pop(item_key)
                layout.removeWidget(widget)
                widget.deleteLater()

        if not items:
            if tab.placeholder is None:
                tab.placeholder = QLabel(empty_text)
                tab.placeholder.setObjectName("listPlaceholder")
                tab.placeholder.setProperty("role", "faint")
                layout.insertWidget(0, tab.placeholder)
        elif tab.placeholder is not None:
            layout.removeWidget(tab.placeholder)
            tab.placeholder.deleteLater()
            tab.placeholder = None

    def _open_settings(self):
        dialog = SettingsDialog(theme.current_theme(), self._on_theme_changed, parent=self)
        dialog.exec()

    def _on_theme_changed(self, key):
        if key == theme.current_theme():
            return

        theme.set_theme(key)
        self._settings.set_theme(key)

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_app_stylesheet())

        self._rebuild_ui()

    def _rebuild_ui(self):
        self.audio.stop_monitoring()

        for page in self._pages.values():
            if hasattr(page, "cards"):
                page.cards.clear()

        old = self.centralWidget()
        self._pages.clear()
        self._nav_buttons.clear()

        self._setup_ui()

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_app_stylesheet())
            app.processEvents()

        if old is not None:
            old.deleteLater()

        self.refresh_ui()
        self.audio.start_monitoring(interval=config.MONITOR_INTERVAL_SECONDS)

    def on_audio_changed(self):
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        self._audio_changed_signal.emit()

    def refresh_ui(self):
        self._refresh_scheduled = False
        self.audio.refresh_devices()
        self.audio.refresh_streams()

        streaming_enabled = self.streaming_mixer.is_enabled()
        if streaming_enabled != self._last_streaming_enabled:
            self._last_streaming_enabled = streaming_enabled
            self._routed_stream_indices.clear()

        if "outputs" in self._pages:
            self._fill_devices("outputs", DeviceType.SINK, False)
        if "inputs" in self._pages:
            self._fill_devices("inputs", DeviceType.SOURCE, True)

        if self.streams_supported:
            if "playback" in self._pages:
                self._fill_streams("playback", DeviceType.SINK_INPUT, DeviceType.SINK)
            if "recording" in self._pages:
                self._fill_streams("recording", DeviceType.SOURCE_OUTPUT, DeviceType.SOURCE)

    def closeEvent(self, event):
        self.audio.stop_monitoring()
        if self.streaming_mixer.is_enabled():
            self.streaming_mixer.disable()
        super().closeEvent(event)