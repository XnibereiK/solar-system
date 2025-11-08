from enum import Enum


class InstallType(str, Enum):
    DC = "DC"
    AC_1PH = "AC_1PH"
    AC_3PH = "AC_3PH"


class ConductorMaterial(str, Enum):
    CU = "Cu"
    AL = "Al"


class Insulation(str, Enum):
    THHN = "THHN"
    XLPE = "XLPE"
    PVC = "PVC"


class InstallationMethod(str, Enum):
    CONDUIT = "conduit"
    TRAY = "tray"
    OPEN_AIR = "open_air"
