from abc import ABC, abstractmethod
from typing import List

from src.core.models import AudioDevice, AudioStream, DeviceType


class AudioBackend(ABC):
    name: str = "Unknown backend"

    @abstractmethod
    def is_available(self) -> bool:
        ...

    def missing_requirements(self) -> List[str]:
        return []

    @abstractmethod
    def list_devices(self, device_type: DeviceType) -> List[AudioDevice]:
        ...

    @abstractmethod
    def set_default_device(self, device: AudioDevice) -> bool:
        ...

    @abstractmethod
    def set_volume(self, device: AudioDevice, volume: float) -> bool:
        ...

    @abstractmethod
    def set_mute(self, device: AudioDevice, mute: bool) -> bool:
        ...

    def list_streams(self, stream_type: DeviceType) -> List[AudioStream]:
        return []

    def set_stream_volume(self, stream: AudioStream, volume: float) -> bool:
        return False

    def set_stream_mute(self, stream: AudioStream, mute: bool) -> bool:
        return False

    def move_stream(self, stream: AudioStream, target_device: AudioDevice) -> bool:
        return False

    def supports_streams(self) -> bool:
        return False

    def supports_per_device_volume(self) -> bool:
        return True

    def get_status_info(self) -> str:
        return ""