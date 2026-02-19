def calc_w18(aadt_total: float, pct_trucks: float, dd: float, dl: float,
             truck_factor: float, growth_pct: float, years: int) -> float:
    """Mantenido por compatibilidad histórica."""
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


def compute_esals_detailed(
    vehicle_classes: list[dict],
    mode: str,
    tpda_total: float,
    dd: float,
    dl: float,
    apply_growth: bool,
    growth_pct: float,
    years: int,
) -> dict:
    """
    Metodología AASHTO 93 detallada por tipo de vehículo.

    Paso 1: ADT_i
      - share_pct: ADT_i = TPDA * (participación_i/100)
      - count:     ADT_i = tránsito_i capturado
    Paso 2: ESAL_i = ADT_i * EALF_i * 365 * B
    Paso 3: ΣESAL = suma(ESAL_i)
    Paso 4: W18 = ΣESAL * DD * DL
    """
    if years <= 0:
        raise ValueError("años de diseño > 0")
    if tpda_total <= 0:
        raise ValueError("TPDA total > 0")
    if dd < 0 or dl < 0:
        raise ValueError("DD y DL deben ser >= 0")
    if apply_growth and growth_pct < 0:
        raise ValueError("Si aplicas crecimiento, la tasa debe ser >= 0")
    if not vehicle_classes:
        raise ValueError("Debes capturar al menos una clase vehicular")

    if apply_growth:
        r = growth_pct / 100.0
        if abs(r) < 1e-12:
            b = float(years)
        else:
            b = ((1 + r) ** years - 1.0) / r
    else:
        b = float(years)

    enabled_rows = [row for row in vehicle_classes if bool(row.get("enabled", True))]
    if not enabled_rows:
        raise ValueError("Debes habilitar al menos un tipo vehicular")

    total_share_pct = 0.0
    total_adt = 0.0
    total_esal = 0.0
    rows = []

    for row in enabled_rows:
        name = row.get("name", "Clase")
        share_pct = float(row.get("share_pct", 0.0))
        count = float(row.get("count", 0.0))
        ealf = float(row.get("ealf", 0.0))

        if share_pct < 0 or count < 0 or ealf < 0:
            raise ValueError("participación, tránsito y EALF deben ser >= 0")

        if mode == "share_pct":
            adt_i = tpda_total * (share_pct / 100.0)
            total_share_pct += share_pct
        else:
            adt_i = count

        esal_i = adt_i * ealf * 365.0 * b
        total_adt += adt_i
        total_esal += esal_i
        rows.append({
            "name": name,
            "share_pct": share_pct,
            "count": count,
            "ealf": ealf,
            "ADT_i": adt_i,
            "ESAL_i": esal_i,
        })

    if mode == "share_pct" and not (99.5 <= total_share_pct <= 100.5):
        raise ValueError(f"La suma de participación debe ser ≈100% (actual {total_share_pct:.2f}%)")

    if mode == "count" and abs(total_adt - tpda_total) > 1e-6:
        raise ValueError(f"La suma de tránsito por tipo ({total_adt:.2f}) debe ser igual al TPDA ({tpda_total:.2f})")

    w18 = total_esal * dd * dl
    return {
        "mode": mode,
        "B": b,
        "total_share_pct": total_share_pct,
        "sum_esal": total_esal,
        "W18": w18,
        "rows": rows,
    }
