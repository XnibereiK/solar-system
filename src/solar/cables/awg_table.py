from __future__ import annotations

from typing import List, Dict


# AWG areas in mm^2 (nominal) for sizes commonly used in power
AWG_SIZES: List[str] = [
    "14",
    "12",
    "10",
    "8",
    "6",
    "4",
    "3",
    "2",
    "1",
    "1/0",
    "2/0",
    "3/0",
    "4/0",
]

AWG_AREA_MM2: Dict[str, float] = {
    "14": 2.08,
    "12": 3.31,
    "10": 5.26,
    "8": 8.37,
    "6": 13.30,
    "4": 21.15,
    "3": 26.67,
    "2": 33.62,
    "1": 42.41,
    "1/0": 53.49,
    "2/0": 67.43,
    "3/0": 85.01,
    "4/0": 107.2,
}


def all_awg_sorted_small_to_large() -> List[str]:
    return AWG_SIZES
