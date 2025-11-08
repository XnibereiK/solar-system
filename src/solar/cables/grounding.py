from __future__ import annotations

from typing import Optional


# Conservative mapping from OCPD rating (A) to minimum Cu grounding AWG (approximate)
GROUND_CU_FOR_OCPD = [
    (20, "12"),
    (60, "10"),
    (100, "8"),
    (200, "6"),
    (300, "4"),
    (400, "3"),
    (600, "2"),
    (800, "1"),
    (1100, "1/0"),
]


def recommend_ground_cu_awg(ocpd_a: Optional[float]) -> Optional[str]:
    if not ocpd_a or ocpd_a <= 0:
        return None
    for limit, awg in GROUND_CU_FOR_OCPD:
        if ocpd_a <= limit:
            return awg
    return "2/0"
