import platform
import threading
import time

from src.core.backends.base import AudioBackend
from src.core.models import DeviceType


def _detect_backend() -> AudioBackend:
    if platform.system() != "Linux":
        raise RuntimeError(
            f"Audio Manager only supports Linux (PipeWire/WirePlumber). Detected: {platform.system()}."
        )
    from src.core.backends.linux import LinuxPipeWireBackend
    return LinuxPipeWireBackend()


class AudioManager:
    def __init__(self, backend: AudioBackend | None = None):
        self.backend = backend or _detect_backend()
        self._devices_cache = {}
        self._streams_cache = {}
        self._callbacks = []
        self._monitor_thread = None
        self._monitoring = False
        self._lock = threading.RLock()

    @property
    def backend_name(self) -> str:
        return self.backend.name

    def is_backend_available(self) -> bool:
        return self.backend.is_available()

    def missing_requirements(self):
        return self.backend.missing_requirements()

    def supports_streams(self) -> bool:
        return self.backend.supports_streams()

    def supports_per_device_volume(self) -> bool:
        return self.backend.supports_per_device_volume()

    def add_callback(self, cb):
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    def remove_callback(self, cb):
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    def _notify_callbacks(self):
        for cb in list(self._callbacks):
            try:
                cb()
            except Exception:
                pass

    def refresh_devices(self):
        with self._lock:
            for dtype in (DeviceType.SINK, DeviceType.SOURCE):
                try:
                    self._devices_cache[dtype] = self.backend.list_devices(dtype)
                except Exception:
                    self._devices_cache[dtype] = []
            return dict(self._devices_cache)

    def get_devices(self, dtype):
        with self._lock:
            if dtype not in self._devices_cache:
                self.refresh_devices()
            return list(self._devices_cache.get(dtype, []))

    def set_default_device(self, device) -> bool:
        if self.backend.set_default_device(device):
            self.refresh_devices()
            self._notify_callbacks()
            return True
        return False

    def set_volume(self, device, volume) -> bool:
        safe_volume = max(0.0, min(1.0, volume))
        if self.backend.set_volume(device, safe_volume):
            device.volume = safe_volume
            self._notify_callbacks()
            return True
        return False

    def set_mute(self, device, mute) -> bool:
        if self.backend.set_mute(device, mute):
            device.mute = mute
            self._notify_callbacks()
            return True
        return False

    def refresh_streams(self):
        if not self.backend.supports_streams():
            with self._lock:
                self._streams_cache = {}
            return {}

        with self._lock:
            for stype in (DeviceType.SINK_INPUT, DeviceType.SOURCE_OUTPUT):
                try:
                    self._streams_cache[stype] = self.backend.list_streams(stype)
                except Exception:
                    self._streams_cache[stype] = []
            return dict(self._streams_cache)

    def get_streams(self, stype):
        with self._lock:
            if stype not in self._streams_cache:
                self.refresh_streams()
            return list(self._streams_cache.get(stype, []))

    def set_stream_volume(self, stream, volume) -> bool:
        safe_volume = max(0.0, min(1.0, volume))
        if self.backend.set_stream_volume(stream, safe_volume):
            stream.volume = safe_volume
            self._notify_callbacks()
            return True
        return False

    def set_stream_mute(self, stream, mute) -> bool:
        if self.backend.set_stream_mute(stream, mute):
            stream.mute = mute
            self._notify_callbacks()
            return True
        return False

    def move_stream(self, stream, target_device) -> bool:
        if self.backend.move_stream(stream, target_device):
            self.refresh_streams()
            self._notify_callbacks()
            return True
        return False

    def get_status_info(self) -> str:
        return self.backend.get_status_info()

    def start_monitoring(self, interval=1.0):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False

    def _monitor_loop(self, interval):
        while self._monitoring:
            try:
                self.refresh_devices()
                self.refresh_streams()
                self._notify_callbacks()
            except Exception:
                pass
            time.sleep(interval)


_audio_manager_instance = None


def get_audio_manager() -> AudioManager:
    global _audio_manager_instance
    if _audio_manager_instance is None:
        _audio_manager_instance = AudioManager()
    return _audio_manager_instance