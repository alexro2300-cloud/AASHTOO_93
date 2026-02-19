def calc_w18(aadt_total: float, pct_trucks: float, dd: float, dl: float,
             truck_factor: float, growth_pct: float, years: int) -> float:
    """W18 acumulado con TPDA y TF."""
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


def calc_w18_from_daily_esal(daily_esal: float, dd: float, dl: float, growth_pct: float, years: int) -> float:
    """W18 desde ESAL diario total por clases (sin usar %pesados ni TF)."""
    if years <= 0:
        raise ValueError("Años de diseño debe ser > 0")
    if daily_esal < 0 or dd < 0 or dl < 0:
        raise ValueError("daily_esal, dd y dl deben ser >= 0")
    g = growth_pct / 100.0
    base = 365.0 * daily_esal * dd * dl
    if abs(g) < 1e-12:
        return base * years
    factor = ((1 + g) ** years - 1.0) / g
    return base * factor


def calc_truck_factor_detailed(vehicle_classes: list[dict], mode: str = "share_pct", aadt_total: float | None = None) -> tuple[float, dict]:
    """
    mode='share_pct': TF = Σ(share_i * ealf_i * ap_i)
    mode='count': calcula ESAL diario = Σ(count_i * ealf_i * ap_i) y valida suma de conteos ≈ TPDA.
    """
    if not vehicle_classes:
        raise ValueError("Debes ingresar al menos una clase vehicular")

    enabled_count = 0
    total_share = 0.0
    total_count = 0.0
    tf = 0.0
    daily_esal = 0.0
    breakdown = {}

    for row in vehicle_classes:
        enabled = bool(row.get("enabled", True))
        if not enabled:
            continue
        enabled_count += 1

        name = row.get("name", "Clase")
        share_pct = float(row.get("share_pct", 0.0))
        count = float(row.get("count", 0.0))
        ealf = float(row.get("ealf", 0.0))
        ap = float(row.get("ap", 1.0))

        if share_pct < 0 or ealf < 0 or ap < 0 or count < 0:
            raise ValueError("Participación, tránsito, EALF y Ap por clase deben ser >= 0")

        if mode == "count":
            contrib_daily = count * ealf * ap
            daily_esal += contrib_daily
            total_count += count
            breakdown[name] = {
                "count": count,
                "ealf": ealf,
                "ap": ap,
                "daily_esal_contribution": contrib_daily,
            }
        else:
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

    if mode == "count":
        if total_count <= 0:
            raise ValueError("La suma de tránsito por clase debe ser > 0")
        if aadt_total is not None and abs(total_count - aadt_total) > 1e-6:
            raise ValueError(f"La suma de tránsito por clases ({total_count:.2f}) debe ser igual al TPDA ({aadt_total:.2f})")
        tf_equivalent = daily_esal / total_count
        return tf_equivalent, {
            "mode": "count",
            "total_count": total_count,
            "daily_esal": daily_esal,
            "classes": breakdown,
        }

    if total_share <= 0:
        raise ValueError("La suma de participaciones vehiculares debe ser > 0")
    if total_share > 100.001:
        raise ValueError("La suma de participaciones vehiculares no puede superar 100%")

    return tf, {
        "mode": "share_pct",
        "total_share_pct": total_share,
        "classes": breakdown,
    }
