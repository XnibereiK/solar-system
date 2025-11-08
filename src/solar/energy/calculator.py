from __future__ import annotations

from .devices import DeviceList


def compute_energy_summaries(device_list: DeviceList) -> dict:
    total_wh = device_list.total_wh_per_day()
    return {
        "total_wh_per_day": total_wh,
        "total_kwh_per_day": total_wh / 1000.0,
        "avg_power_w": total_wh / 24.0,
        "device_count": len(device_list.devices),
    }
