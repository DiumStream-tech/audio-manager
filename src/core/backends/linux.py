import os
import re
import shutil
import subprocess
from typing import List

from src.core import app_registry
from src.core.backends.base import AudioBackend
from src.core.icon_resolver import resolve_icon_url
from src.core.models import AudioDevice, AudioStream, DeviceState, DeviceType


class LinuxPipeWireBackend(AudioBackend):
    name = "PipeWire / WirePlumber (Linux)"
    REQUIRED_TOOLS = ["pactl", "wpctl"]

    def __init__(self):
        self._missing = [tool for tool in self.REQUIRED_TOOLS if shutil.which(tool) is None]

    def is_available(self) -> bool:
        return not self._missing

    def missing_requirements(self) -> List[str]:
        if not self._missing:
            return []
        return [
            f"Missing command: {tool} (install pipewire-pulse / wireplumber)"
            for tool in self._missing
        ]

    def supports_streams(self) -> bool:
        return True

    def _run(self, cmd):
        env = dict(os.environ, LC_ALL="C", LANGUAGE="C")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, env=env)
            return result.returncode, result.stdout, result.stderr
        except Exception as exc:
            return -1, "", str(exc)

    def _default_device_name(self, device_type: DeviceType) -> str:
        cmd = ["pactl", "get-default-sink"] if device_type == DeviceType.SINK else ["pactl", "get-default-source"]
        code, out, _ = self._run(cmd)
        return out.strip() if code == 0 else ""

    def list_devices(self, device_type: DeviceType) -> List[AudioDevice]:
        cmd = ["pactl", "list", "sinks"] if device_type == DeviceType.SINK else ["pactl", "list", "sources"]
        code, out, _ = self._run(cmd)
        if code != 0:
            return []
        return self._parse_device_list(out, device_type)

    def _parse_device_list(self, output: str, device_type: DeviceType) -> List[AudioDevice]:
        devices = []
        current = None
        header = f"{device_type.value.capitalize()} #"
        default_name = self._default_device_name(device_type)

        for raw in output.splitlines():
            line = raw.strip()

            if line.startswith(header):
                if current:
                    devices.append(current)
                match = re.search(r"#(\d+)", line)
                idx = int(match.group(1)) if match else len(devices)
                current = AudioDevice(index=idx, name="", description="", device_type=device_type)
                continue

            if current is None:
                continue

            if line.startswith("Name: "):
                current.name = line[len("Name: "):].strip()
            elif line.startswith("Description: "):
                current.description = line[len("Description: "):].strip()
            elif line.startswith("State: "):
                raw_state = line[len("State: "):].strip().lower()
                try:
                    current.state = DeviceState(raw_state)
                except ValueError:
                    current.state = DeviceState.UNKNOWN
            elif line.startswith("Volume: "):
                match = re.search(r"(\d+)%", line)
                if match:
                    current.volume = min(int(match.group(1)) / 100.0, 1.0)
            elif line.startswith("Mute: "):
                current.mute = line[len("Mute: "):].strip().lower() == "yes"
            elif line.startswith("Driver: "):
                current.driver = line[len("Driver: "):].strip()
            elif line.startswith("device.form_factor = "):
                current.properties["form_factor"] = line[len("device.form_factor = "):].strip().strip('"')

        if current:
            devices.append(current)

        for device in devices:
            device.is_default = bool(default_name) and device.name == default_name

        return devices

    def set_default_device(self, device: AudioDevice) -> bool:
        verb = "set-default-sink" if device.device_type == DeviceType.SINK else "set-default-source"
        code, _, _ = self._run(["pactl", verb, device.name])
        return code == 0

    def set_volume(self, device: AudioDevice, volume: float) -> bool:
        pct = int(max(0.0, min(1.0, volume)) * 100)
        verb = "set-sink-volume" if device.device_type == DeviceType.SINK else "set-source-volume"
        code, _, _ = self._run(["pactl", verb, device.name, f"{pct}%"])
        return code == 0

    def set_mute(self, device: AudioDevice, mute: bool) -> bool:
        verb = "set-sink-mute" if device.device_type == DeviceType.SINK else "set-source-mute"
        code, _, _ = self._run(["pactl", verb, device.name, "1" if mute else "0"])
        return code == 0

    def list_streams(self, stream_type: DeviceType) -> List[AudioStream]:
        cmd = ["pactl", "list", "sink-inputs"] if stream_type == DeviceType.SINK_INPUT else ["pactl", "list", "source-outputs"]
        code, out, _ = self._run(cmd)
        if code != 0:
            return []
        return self._parse_streams(out, stream_type)

    def _parse_streams(self, output: str, stype: DeviceType) -> List[AudioStream]:
        header = "Sink Input #" if stype == DeviceType.SINK_INPUT else "Source Output #"
        streams = []
        current = None

        for raw in output.splitlines():
            line = raw.strip()

            if line.startswith(header):
                if current:
                    streams.append(current)
                match = re.search(r"#(\d+)", line)
                idx = int(match.group(1)) if match else len(streams)
                current = AudioStream(index=idx, name="", device_type=stype, device_index=-1)
                continue

            if current is None:
                continue

            if "application.name" in line and "=" in line:
                current.application_name = line.split("=", 1)[1].strip().strip('"')
                current.name = current.application_name or current.name
            elif "application.process.binary" in line and "=" in line:
                current.binary = line.split("=", 1)[1].strip().strip('"')
            elif "application.process.id" in line and "=" in line:
                try:
                    current.pid = int(line.split("=", 1)[1].strip().strip('"'))
                except ValueError:
                    pass
            elif line.startswith("Sink: ") or line.startswith("Source: "):
                match = re.search(r"(\d+)", line)
                if match:
                    current.device_index = int(match.group(1))
            elif line.startswith("Volume: "):
                match = re.search(r"(\d+)%", line)
                if match:
                    current.volume = min(int(match.group(1)) / 100.0, 1.0)
            elif line.startswith("Mute: "):
                current.mute = line[len("Mute: "):].strip().lower() == "yes"

        if current:
            streams.append(current)

        cleaned = []
        seen_canonical = set()

        for stream in streams:
            raw_name = stream.application_name or stream.name or ""
            resolution = app_registry.resolve_stream_name(raw_name)

            # resolution is None  → explicitly ignored binary (e.g. pipewire, systemd)
            if resolution is None:
                continue

            if resolution is False:
                # Unknown app: not in registry → hide it.
                # Add it to apps.json to make it appear.
                continue

            display_name = resolution["label"]
            slug = resolution.get("slug", "")

            if display_name in seen_canonical:
                continue

            seen_canonical.add(display_name)
            stream.application_name = display_name
            stream.name = display_name
            stream.application_icon_url = resolve_icon_url(slug)

            cleaned.append(stream)

        return cleaned

    def set_stream_volume(self, stream: AudioStream, volume: float) -> bool:
        # Bug fix: clamp to 1.0 max (100%) — was previously allowing 150%.
        pct = int(max(0.0, min(1.0, volume)) * 100)
        verb = "set-sink-input-volume" if stream.device_type == DeviceType.SINK_INPUT else "set-source-output-volume"
        code, _, _ = self._run(["pactl", verb, str(stream.index), f"{pct}%"])
        return code == 0

    def set_stream_mute(self, stream: AudioStream, mute: bool) -> bool:
        verb = "set-sink-input-mute" if stream.device_type == DeviceType.SINK_INPUT else "set-source-output-mute"
        code, _, _ = self._run(["pactl", verb, str(stream.index), "1" if mute else "0"])
        return code == 0

    def move_stream(self, stream: AudioStream, target_device: AudioDevice) -> bool:
        if stream.device_type == DeviceType.SINK_INPUT and target_device.device_type == DeviceType.SINK:
            cmd = ["pactl", "move-sink-input", str(stream.index), target_device.name]
        elif stream.device_type == DeviceType.SOURCE_OUTPUT and target_device.device_type == DeviceType.SOURCE:
            cmd = ["pactl", "move-source-output", str(stream.index), target_device.name]
        else:
            return False

        code, _, _ = self._run(cmd)
        return code == 0

    def get_status_info(self) -> str:
        code, out, _ = self._run(["wpctl", "status"])
        return out if code == 0 else "wpctl unavailable"
