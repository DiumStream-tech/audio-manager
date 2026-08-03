from src import __version__


APP_NAME = "Audio Manager"
APP_VERSION = __version__

WINDOW_DEFAULT_SIZE = (1040, 680)
WINDOW_MIN_SIZE = (860, 560)

GITHUB_UPDATES_ENABLED = True
GITHUB_URL = "https://github.com/DiumStream-tech/audio-manager"

MONITOR_INTERVAL_SECONDS = 1.5

ICON_FETCH_TIMEOUT_SECONDS = 5
HTTP_USER_AGENT = f"{APP_NAME.replace(' ', '')}/{APP_VERSION}"

STREAMING_SINK_PREFIX = "audiomanager_"
STREAMING_CHANNELS = [
    ("game", "Jeu"),
    ("chat", "Chat / Voice"),
    ("media", "Média"),
    ("music", "Musique"),
]

STREAMING_LOOPBACK_LATENCY_MS = 20
STREAMING_TOGGLE_UNMUTE_DELAY_MS = 500

VOLUME_SAFETY_THRESHOLD = 0.70

CARD_ENTER_ANIMATION_MS = 180
CARD_HOVER_ANIMATION_MS = 120
PANEL_FADE_ANIMATION_MS = 160
