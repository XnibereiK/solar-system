from __future__ import annotations

from typing import Dict

# Very conservative base ampacity (A) for Cu THHN in conduit at 30C, single conductor
# These are simplified values for demonstration; users must verify against local codes and specific installation conditions.
BASE_AMPACITY_CU_THHN_30C: Dict[str, int] = {
    "14": 20,
    "12": 25,
    "10": 35,
    "8": 50,
    "6": 65,
    "4": 85,
    "3": 100,
    "2": 115,
    "1": 130,
    "1/0": 150,
    "2/0": 175,
    "3/0": 200,
    "4/0": 230,
}


def temp_correction_factor(ambient_c: float) -> float:
    # Approximate derating for THHN per NEC 310.15(B)(1):
    # 30C: 1.0, 40C: 0.91, 50C: 0.82, 60C: 0.71
    if ambient_c <= 30:
        return 1.0
    elif ambient_c <= 40:
        return 0.91
    elif ambient_c <= 50:
        return 0.82
    elif ambient_c <= 60:
        return 0.71
    else:
        return 0.6
