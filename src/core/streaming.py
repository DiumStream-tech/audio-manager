import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src import config
from src.core.settings import get_settings_store

MONITOR_MIX_ID = "monitor"
STREAM_MIX_ID = "stream"

MONITOR_SINK_NAME = f"{config.STREAMING_SINK_PREFIX}monitor"
MONITOR_SINK_DESC = "AudioManager-Casque"
STREAM_SINK_NAME = f"{config.STREAMING_SINK_PREFIX}stream"
STREAM_SINK_DESC = "AudioManager-Diffusion"


@dataclass
class StreamingChannel:
    id: str
    label: str
    sink_name: str
    monitor_volume: float = 1.0
    stream_volume: float = 1.0
    monitor_mute: bool = False
    stream_mute: bool = False
    linked: bool = False
    _monitor_input_index: Optional[int] = field(default=None, repr=False)
    _stream_input_index: Optional[int] = field(default=None, repr=False)


class StreamingMixer:
    """Gère la création / suppression des sinks virtuels du mode streaming."""

    def __init__(self):
        self._enabled = False
        self._module_ids: List[int] = []
        self._restore_default_sink: str = ""
        self._internal_sink_input_indices: set = set()
        self._internal_source_output_indices: set = set()
        self.channels: Dict[str, StreamingChannel] = {
            cid: StreamingChannel(id=cid, label=label, sink_name=f"{config.STREAMING_SINK_PREFIX}{cid}")
            for cid, label in config.STREAMING_CHANNELS
        }

        self._settings = get_settings_store()
        self._restore_channel_settings()

    def _restore_channel_settings(self):
        for channel in self.channels.values():
            saved = self._settings.get_channel_settings(channel.id)
            if not saved:
                continue
            channel.monitor_volume = float(saved.get("monitor_volume", channel.monitor_volume))
            channel.stream_volume = float(saved.get("stream_volume", channel.stream_volume))
            channel.monitor_mute = bool(saved.get("monitor_mute", channel.monitor_mute))
            channel.stream_mute = bool(saved.get("stream_mute", channel.stream_mute))
            channel.linked = bool(saved.get("linked", channel.linked))

    def _save_channel_settings(self, channel: "StreamingChannel"):
        self._settings.set_channel_settings(channel.id, {
            "monitor_volume": channel.monitor_volume,
            "stream_volume": channel.stream_volume,
            "monitor_mute": channel.monitor_mute,
            "stream_mute": channel.stream_mute,
            "linked": channel.linked,
        })

    def is_available(self) -> bool:
        return shutil.which("pactl") is not None

    def is_enabled(self) -> bool:
        return self._enabled

    def _run(self, cmd):
        env = dict(os.environ, LC_ALL="C", LANGUAGE="C")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=env)
            return result.returncode, result.stdout, result.stderr
        except Exception as exc:
            return -1, "", str(exc)

    def _load_module(self, args: List[str]) -> Optional[int]:
        code, out, _ = self._run(["pactl", "load-module"] + args)
        if code != 0:
            return None
        try:
            module_id = int(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return None
        self._module_ids.append(module_id)
        return module_id

    def _default_sink_name(self) -> str:
        code, out, _ = self._run(["pactl", "get-default-sink"])
        return out.strip() if code == 0 else ""

    def _stream_index_for_module(self, module_id: Optional[int], list_target: str, header: str) -> Optional[int]:
        """Retrouve l'index du sink-input / source-output créé par un module donné.

        `list_target` vaut "sink-inputs" ou "source-outputs", `header` le
        préfixe correspondant ("Sink Input #" ou "Source Output #").
        """
        if module_id is None:
            return None

        code, out, _ = self._run(["pactl", "list", list_target])
        if code != 0:
            return None

        current_index = None
        for raw in out.splitlines():
            line = raw.strip()
            match = re.match(rf"{header}(\d+)", line)
            if match:
                current_index = int(match.group(1))
                continue
            if line.startswith("Owner Module:") and current_index is not None:
                owner = line[len("Owner Module:"):].strip()
                if owner.isdigit() and int(owner) == module_id:
                    return current_index

        return None

    def _sink_input_index_for_module(self, module_id: Optional[int]) -> Optional[int]:
        """Retrouve l'index du sink-input créé par un module-loopback donné."""
        return self._stream_index_for_module(module_id, "sink-inputs", "Sink Input #")

    def _source_output_index_for_module(self, module_id: Optional[int]) -> Optional[int]:
        """Retrouve l'index du source-output créé par un module-loopback donné."""
        return self._stream_index_for_module(module_id, "source-outputs", "Source Output #")

    def _track_loopback_module(self, module_id: Optional[int]) -> Optional[int]:
        """Enregistre les deux entrées (sink-input + source-output) créées
        par un module-loopback, pour pouvoir les cacher dans les onglets
        Lecture et Enregistrement. Retourne l'index sink-input (utilisé pour
        piloter le volume/mute de ce mix)."""
        sink_input_index = self._sink_input_index_for_module(module_id)
        source_output_index = self._source_output_index_for_module(module_id)
        if sink_input_index is not None:
            self._internal_sink_input_indices.add(sink_input_index)
        if source_output_index is not None:
            self._internal_source_output_indices.add(source_output_index)
        return sink_input_index


    def enable(self) -> bool:
        """Crée les sinks du mode streaming. Ne fait rien si déjà actif."""
        if self._enabled:
            return True
        if not self.is_available():
            return False

        self._restore_default_sink = self._default_sink_name()

        ok = self._load_module([
            "module-null-sink",
            f"sink_name={MONITOR_SINK_NAME}",
            f"sink_properties=device.description={MONITOR_SINK_DESC}",
        ])
        ok2 = self._load_module([
            "module-null-sink",
            f"sink_name={STREAM_SINK_NAME}",
            f"sink_properties=device.description={STREAM_SINK_DESC}",
        ])
        if ok is None or ok2 is None:
            self.disable()
            return False

        if self._restore_default_sink:
            output_module = self._load_module([
                "module-loopback",
                f"source={MONITOR_SINK_NAME}.monitor",
                f"sink={self._restore_default_sink}",
                f"latency_msec={config.STREAMING_LOOPBACK_LATENCY_MS}",
            ])
            self._track_loopback_module(output_module)

        for channel in self.channels.values():
            channel_ok = self._load_module([
                "module-null-sink",
                f"sink_name={channel.sink_name}",
                f"sink_properties=device.description={channel.label}",
            ])
            if channel_ok is None:
                continue

            monitor_module = self._load_module([
                "module-loopback",
                f"source={channel.sink_name}.monitor",
                f"sink={MONITOR_SINK_NAME}",
                f"latency_msec={config.STREAMING_LOOPBACK_LATENCY_MS}",
            ])
            stream_module = self._load_module([
                "module-loopback",
                f"source={channel.sink_name}.monitor",
                f"sink={STREAM_SINK_NAME}",
                f"latency_msec={config.STREAMING_LOOPBACK_LATENCY_MS}",
            ])

            channel._monitor_input_index = self._track_loopback_module(monitor_module)
            channel._stream_input_index = self._track_loopback_module(stream_module)

            self._apply_channel_volume(channel, MONITOR_MIX_ID)
            self._apply_channel_volume(channel, STREAM_MIX_ID)
            self._apply_channel_mute(channel, MONITOR_MIX_ID)
            self._apply_channel_mute(channel, STREAM_MIX_ID)

        self._enabled = True
        return True

    def disable(self):
        for module_id in reversed(self._module_ids):
            self._run(["pactl", "unload-module", str(module_id)])
        self._module_ids.clear()
        self._internal_sink_input_indices.clear()
        self._internal_source_output_indices.clear()

        for channel in self.channels.values():
            channel._monitor_input_index = None
            channel._stream_input_index = None

        self._enabled = False

    def _apply_channel_volume(self, channel: StreamingChannel, mix: str) -> bool:
        index = channel._monitor_input_index if mix == MONITOR_MIX_ID else channel._stream_input_index
        if index is None:
            return False
        volume = channel.monitor_volume if mix == MONITOR_MIX_ID else channel.stream_volume
        pct = int(max(0.0, min(1.0, volume)) * 100)
        code, _, _ = self._run(["pactl", "set-sink-input-volume", str(index), f"{pct}%"])
        return code == 0

    def _apply_channel_mute(self, channel: StreamingChannel, mix: str) -> bool:
        index = channel._monitor_input_index if mix == MONITOR_MIX_ID else channel._stream_input_index
        if index is None:
            return False
        mute = channel.monitor_mute if mix == MONITOR_MIX_ID else channel.stream_mute
        code, _, _ = self._run(["pactl", "set-sink-input-mute", str(index), "1" if mute else "0"])
        return code == 0

    def set_channel_volume(self, channel_id: str, mix: str, volume: float) -> bool:
        channel = self.channels.get(channel_id)
        if channel is None or not self._enabled:
            return False

        volume = max(0.0, min(1.0, volume))
        targets = [mix]
        if channel.linked:
            targets = [MONITOR_MIX_ID, STREAM_MIX_ID]

        success = True
        for target in targets:
            if target == MONITOR_MIX_ID:
                channel.monitor_volume = volume
            else:
                channel.stream_volume = volume
            success = self._apply_channel_volume(channel, target) and success

        self._save_channel_settings(channel)
        return success

    def set_channel_mute(self, channel_id: str, mix: str, mute: bool) -> bool:
        channel = self.channels.get(channel_id)
        if channel is None or not self._enabled:
            return False

        if mix == MONITOR_MIX_ID:
            channel.monitor_mute = mute
        else:
            channel.stream_mute = mute

        result = self._apply_channel_mute(channel, mix)
        self._save_channel_settings(channel)
        return result

    def set_channel_linked(self, channel_id: str, linked: bool):
        channel = self.channels.get(channel_id)
        if channel is None:
            return
        channel.linked = linked
        if linked:
            # En passant en mode lié, on aligne le mix "Diffusion" sur le
            # "Casque" — comme le fait Sonar quand on relie les deux faders.
            # (set_channel_volume sauvegarde déjà les réglages du canal.)
            self.set_channel_volume(channel_id, MONITOR_MIX_ID, channel.monitor_volume)
        else:
            self._save_channel_settings(channel)

    def channel_sink_name(self, channel_id: str) -> str:
        channel = self.channels.get(channel_id)
        return channel.sink_name if channel else ""

    def internal_stream_indices(self, stype=None):
        """Index des sink-inputs / source-outputs créés par nos propres
        module-loopback (les deux côtés de chaque loopback : le flux qui
        joue dans le mix cible, ET celui qui enregistre depuis le canal
        source). À utiliser pour les exclure des onglets Lecture et
        Enregistrement, qui ne doivent afficher que de vraies applications,
        pas la plomberie interne du mode streaming.

        `stype` : passer DeviceType.SINK_INPUT pour l'onglet Lecture,
        DeviceType.SOURCE_OUTPUT pour l'onglet Enregistrement. Si omis, les
        deux ensembles sont retournés fusionnés (rétrocompatibilité).
        """
        from src.core.models import DeviceType

        if stype == DeviceType.SINK_INPUT:
            return set(self._internal_sink_input_indices)
        if stype == DeviceType.SOURCE_OUTPUT:
            return set(self._internal_source_output_indices)
        return set(self._internal_sink_input_indices) | set(self._internal_source_output_indices)


_mixer_instance = None


def get_streaming_mixer() -> StreamingMixer:
    global _mixer_instance
    if _mixer_instance is None:
        _mixer_instance = StreamingMixer()
    return _mixer_instance
