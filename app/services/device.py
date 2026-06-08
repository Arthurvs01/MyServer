import json
import platform
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .system import get_system_info


def get_network_info() -> Dict[str, object]:
    interfaces: List[Dict[str, object]] = []
    try:
        output = subprocess.check_output(["ip", "-brief", "addr"], text=True, stderr=subprocess.DEVNULL)
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            name = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            addrs = parts[2:] if len(parts) > 2 else []
            interfaces.append({"name": name, "state": state, "addresses": addrs})
    except Exception:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            addr = info[4][0]
            family = "IPv6" if info[0] == socket.AF_INET6 else "IPv4"
            interfaces.append({"name": socket.gethostname(), "state": "unknown", "addresses": [f"{family}:{addr}"]})
    return {"hostname": socket.gethostname(), "interfaces": interfaces}


def get_battery_info() -> Dict[str, object]:
    termux_command = ["termux-battery-status"]
    try:
        output = subprocess.check_output(termux_command, text=True, stderr=subprocess.DEVNULL)
        battery = json.loads(output)
        battery["source"] = "termux-api"
        return battery
    except Exception:
        battery = {}
        battery_path = Path("/sys/class/power_supply/battery")
        if battery_path.exists():
            for field in ["capacity", "status", "voltage_now", "current_now"]:
                path = battery_path / field
                if path.exists():
                    battery[field] = path.read_text().strip()
            battery["source"] = "sysfs"
            return battery
    return {"available": False, "message": "Termux API / sysfs não disponível"}


def get_device_info() -> Dict[str, object]:
    info = get_system_info()
    info["network"] = get_network_info()
    info["battery"] = get_battery_info()
    return info


def perform_device_action(action: str) -> Dict[str, object]:
    if action == "status":
        return get_device_info()
    if action == "battery":
        return get_battery_info()
    if action == "network":
        return get_network_info()
    if action == "reboot":
        return attempt_reboot()
    raise ValueError(f"Ação inválida: {action}")


def attempt_reboot() -> Dict[str, object]:
    candidates = [
        ["su", "-c", "reboot"],
        ["reboot"],
        ["svc", "power", "reboot"],
    ]
    errors = []
    for command in candidates:
        try:
            subprocess.check_call(command, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            return {"result": "Comando de reboot enviado", "command": command}
        except Exception as exc:
            errors.append(str(exc))
    return {"result": "Falha ao reiniciar", "errors": errors}
