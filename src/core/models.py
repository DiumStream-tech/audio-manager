from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class DeviceType(Enum):
    SOURCE = "source"
    SINK = "sink"
    SOURCE_OUTPUT = "source_output"
    SINK_INPUT = "sink_input"


class DeviceState(Enum):
    RUNNING = "running"
    IDLE = "idle"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


@dataclass
class AudioDevice:
    index: int
    name: str
    description: str
    device_type: DeviceType
    state: DeviceState = DeviceState.UNKNOWN
    volume: float = 1.0
    mute: bool = False
    is_default: bool = False
    channels: int = 2
    sample_rate: int = 48000
    driver: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioStream:
    index: int
    name: str
    device_type: DeviceType
    device_index: int
    volume: float = 1.0
    mute: bool = False
    application_name: str = ""
    application_icon_url: str = ""
    pid: int = 0
    binary: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    is_placeholder: bool = False


_HEADPHONE_FORM_FACTORS = {"headphone", "headset", "earbud", "earbuds", "portable"}
_HEADPHONE_KEYWORDS = (
    "headphone",
    "headset",
    "earphone",
    "earbud",
    "airpod",
    "casque",
    "écouteur",
    "ecouteur",
)


def is_headphone_device(device: AudioDevice) -> bool:
    form_factor = str((device.properties or {}).get("form_factor", "")).lower()
    if form_factor in _HEADPHONE_FORM_FACTORS:
        return True
    text = f"{device.name} {device.description}".lower()
    return any(keyword in text for keyword in _HEADPHONE_KEYWORDS)