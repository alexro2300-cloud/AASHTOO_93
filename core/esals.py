def calc_w18(aadt_total: float, pct_trucks: float, dd: float, dl: float,
             truck_factor: float, growth_pct: float, years: int) -> float:
    """
    W18 acumulado con TPDA y factor camión (TF).

    aadt_total: veh/día
    pct_trucks: fracción (0-1)
    dd, dl: factores
    truck_factor: ESAL/veh pesado
    growth_pct: % anual (ej 3)
    years: años
    """
    if years <= 0:
        raise ValueError("Años de diseño debe ser > 0")
    if aadt_total < 0 or pct_trucks < 0 or dd < 0 or dl < 0 or truck_factor < 0:
        raise ValueError("Entradas de tránsito no pueden ser negativas")

    g = growth_pct / 100.0
    base = 365.0 * aadt_total * pct_trucks * dd * dl * truck_factor

    if abs(g) < 1e-12:
        return base * years

    factor = ((1 + g) ** years - 1.0) / g
    return base * factor


def calc_truck_factor_detailed(vehicle_classes: list[dict]) -> tuple[float, dict]:
    """
    Calcula TF ponderado por clases vehiculares.

    vehicle_classes: [{"name": str, "share_pct": float, "ealf": float, "ap": float, "enabled": bool}, ...]
    Retorna (tf, desglose)
    """
    if not vehicle_classes:
        raise ValueError("Debes ingresar al menos una clase vehicular")

    total_share = 0.0
    tf = 0.0
    breakdown = {}

    enabled_count = 0

    for row in vehicle_classes:
        enabled = bool(row.get("enabled", True))
        if not enabled:
            continue
        enabled_count += 1

        name = row.get("name", "Clase")
        share_pct = float(row.get("share_pct", 0.0))
        ealf = float(row.get("ealf", 0.0))
        ap = float(row.get("ap", 1.0))

        if share_pct < 0 or ealf < 0 or ap < 0:
            raise ValueError("Participación, EALF y Ap por clase deben ser >= 0")

        share = share_pct / 100.0
        contrib = share * ealf * ap
        total_share += share_pct
        tf += contrib
        breakdown[name] = {
            "share_pct": share_pct,
            "ealf": ealf,
            "ap": ap,
            "contribution": contrib,
        }

    if enabled_count == 0:
        raise ValueError("Debes habilitar al menos una clase vehicular")

    if total_share <= 0:
        raise ValueError("La suma de participaciones vehiculares debe ser > 0")

    if total_share > 100.001:
        raise ValueError("La suma de participaciones vehiculares no puede superar 100%")

    return tf, {
        "total_share_pct": total_share,
        "classes": breakdown,
    }
