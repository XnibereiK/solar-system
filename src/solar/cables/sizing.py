from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Literal

from .awg_table import AWG_AREA_MM2, AWG_SIZES
from .ampacity import BASE_AMPACITY_CU_THHN_30C, temp_correction_factor
from .grounding import recommend_ground_cu_awg


Material = Literal["Cu", "Al"]
InstallType = Literal["DC", "AC_1PH", "AC_3PH"]


def resistivity_ohm_m(material: Material, ambient_c: float) -> float:
    # 20C base resistivity and temperature coefficient alpha
    if material == "Cu":
        rho20 = 1.724e-8
        alpha = 0.00393
    else:
        rho20 = 2.826e-8
        alpha = 0.00403
    return rho20 * (1 + alpha * (ambient_c - 20.0))


@dataclass
class CableInputs:
    install_type: InstallType
    distance_m: float
    load_w: float
    voltage_v: float
    drop_pct: float
    material: Material
    ambient_c: float = 30.0
    power_factor: float = 1.0
    efficiency: float = 1.0
    ocpd_a: Optional[float] = None


@dataclass
class CableResult:
    awg: str
    area_mm2: float
    current_a: float
    drop_pct: float
    ampacity_a: float
    ampacity_margin_pct: float
    grounding_awg: Optional[str]


def _calc_current(inputs: CableInputs) -> float:
    if inputs.install_type == "AC_3PH":
        denom = math.sqrt(3) * inputs.voltage_v * inputs.power_factor * inputs.efficiency
    else:
        denom = inputs.voltage_v * inputs.power_factor * inputs.efficiency
    return max(0.0, inputs.load_w / denom)


def _path_factor(install_type: InstallType) -> float:
    return math.sqrt(3) if install_type == "AC_3PH" else 2.0


def _required_area_mm2_by_drop(inputs: CableInputs, current_a: float) -> float:
    rho = resistivity_ohm_m(inputs.material, inputs.ambient_c)
    k = _path_factor(inputs.install_type)
    v_drop_max = inputs.voltage_v * (inputs.drop_pct / 100.0)
    # area A = rho * (k*L) * I / Vdrop
    A = rho * (k * inputs.distance_m) * current_a / v_drop_max
    return A * 1e6  # convert from m^2 to mm^2


def _pick_awg_by_area(area_mm2_min: float) -> Optional[str]:
    for awg in AWG_SIZES:
        if AWG_AREA_MM2[awg] >= area_mm2_min:
            return awg
    return None


def _ampacity_for_awg(awg: str, ambient_c: float, material: Material) -> float:
    base = BASE_AMPACITY_CU_THHN_30C.get(awg)
    if base is None:
        return 0.0
    # Material factor: Aluminum conductors typically have lower ampacity than copper for the same size
    material_factor = 1.0 if material == "Cu" else 0.8
    return base * temp_correction_factor(ambient_c) * material_factor


def _calc_drop_pct_for_awg(inputs: CableInputs, current_a: float, awg: str) -> float:
    # Use resistivity and area to recompute R and drop
    rho = resistivity_ohm_m(inputs.material, inputs.ambient_c)
    A = AWG_AREA_MM2[awg] / 1e6  # back to m^2
    k = _path_factor(inputs.install_type)
    r_total = rho * (k * inputs.distance_m) / A
    v_drop = current_a * r_total
    return (v_drop / inputs.voltage_v) * 100.0


def size_cable(inputs: CableInputs) -> CableResult:
    # Validate inputs
    if inputs.distance_m <= 0 or inputs.load_w <= 0 or inputs.voltage_v <= 0:
        raise ValueError("Distance, load, and voltage must be > 0")
    if not (0 < inputs.drop_pct <= 10):
        raise ValueError("Allowable drop must be between 0 and 10%")

    I = _calc_current(inputs)
    area_needed = _required_area_mm2_by_drop(inputs, I)
    awg = _pick_awg_by_area(area_needed)
    if awg is None:
        raise ValueError("Voltage drop requirement cannot be met with available AWG sizes. Increase voltage or drop limit.")

    # Ensure ampacity >= 125% of current (continuous load practice)
    # Note: Ampacity table currently for Cu THHN; if material is Al or insulation differs, this is conservative.
    required_cont = 1.25 * I
    while True:
        ampacity = _ampacity_for_awg(awg, inputs.ambient_c, inputs.material)
        drop_pct = _calc_drop_pct_for_awg(inputs, I, awg)
        if ampacity >= required_cont and drop_pct <= inputs.drop_pct:
            break
        # Upsize to next AWG (larger conductor)
        idx = AWG_SIZES.index(awg)
        if idx + 1 >= len(AWG_SIZES):
            raise ValueError("Constraints cannot be met even with largest AWG.")
        awg = AWG_SIZES[idx + 1]

    margin = (ampacity - required_cont) / required_cont * 100.0
    ground = recommend_ground_cu_awg(inputs.ocpd_a)
    return CableResult(
        awg=awg,
        area_mm2=AWG_AREA_MM2[awg],
        current_a=I,
        drop_pct=drop_pct,
        ampacity_a=ampacity,
        ampacity_margin_pct=margin,
        grounding_awg=ground,
    )
