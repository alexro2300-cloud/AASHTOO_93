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
