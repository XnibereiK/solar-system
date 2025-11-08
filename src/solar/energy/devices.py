from __future__ import annotations

from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    power_w: float = Field(ge=0)
    duty_hours_per_day: float = Field(ge=0, le=24)
    count: int = Field(ge=0)

    @property
    def daily_wh(self) -> float:
        return self.power_w * self.duty_hours_per_day * self.count


class DeviceList(BaseModel):
    devices: List[Device] = Field(default_factory=list)

    def total_wh_per_day(self) -> float:
        return sum(d.daily_wh for d in self.devices)

    def total_kw_per_day(self) -> float:
        return self.total_wh_per_day() / 1000.0

    def avg_power_w(self) -> float:
        return self.total_wh_per_day() / 24.0
