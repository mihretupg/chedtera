from collections.abc import Iterable

ADDIS_ABABA_SUBCITIES = {
    "addis ketema",
    "akaky kaliti",
    "arada",
    "bole",
    "gullele",
    "kirkos",
    "kolfe keranio",
    "lemi kura",
    "lideta",
    "nifas silk-lafto",
    "yeka",
}


def normalize_subcity(value: str) -> str:
    return " ".join(value.strip().lower().split())


def enforce_addis_subcity(value: str, allowed: Iterable[str] = ADDIS_ABABA_SUBCITIES) -> str:
    normalized = normalize_subcity(value)
    if normalized not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise ValueError(f"Subcity must be Addis Ababa only. Allowed: {allowed_list}")
    return normalized
