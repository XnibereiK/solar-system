from solar.energy.devices import Device, DeviceList
from solar.energy.calculator import compute_energy_summaries


def test_energy_summaries_basic():
    devices = DeviceList(
        devices=[
            Device(name="LED Bulb", power_w=10, duty_hours_per_day=5, count=6),  # 300 Wh
            Device(name="Fridge", power_w=120, duty_hours_per_day=8, count=1),   # 960 Wh
        ]
    )
    s = compute_energy_summaries(devices)
    assert abs(s["total_wh_per_day"] - 1260) < 1e-6
    assert abs(s["total_kwh_per_day"] - 1.26) < 1e-6
    assert abs(s["avg_power_w"] - 52.5) < 1e-6
    assert s["device_count"] == 2
