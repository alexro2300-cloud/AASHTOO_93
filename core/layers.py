def _cm_to_in(cm: float) -> float:
    return cm / 2.54


def _in_to_cm(inches: float) -> float:
    return inches * 2.54


def sn_provided(a1, a2, a3, m2, m3, d1_in, d2_in, d3_in) -> float:
    return a1 * d1_in + a2 * m2 * d2_in + a3 * m3 * d3_in


def _iter_grid(min_in: float, max_in: float, step_in: float):
    v = min_in
    while v <= max_in + 1e-9:
        yield v
        v += step_in


def recommend_thicknesses(
    sn_required: float,
    a1: float, a2: float, a3: float,
    m2: float, m3: float,
    step_in: float,
    d1_fixed_in: float,
    d2_min_in: float, d2_max_in: float,
    d3_min_in: float, d3_max_in: float,
):
    """
    Busca el menor (D2,D3) en una malla que cumpla SN.
    Criterio: minimizar (D2 + D3). Unidades en pulgadas.
    """
    if sn_required <= 0:
        raise ValueError("SN requerido debe ser > 0")
    if step_in <= 0:
        raise ValueError("step_in debe ser > 0")

    best = None
    best_sn = -1e9

    for d2 in _iter_grid(d2_min_in, d2_max_in, step_in):
        for d3 in _iter_grid(d3_min_in, d3_max_in, step_in):
            sn = sn_provided(a1, a2, a3, m2, m3, d1_fixed_in, d2, d3)
            if sn > best_sn:
                best_sn = sn
            if sn >= sn_required:
                obj = d2 + d3
                if (best is None) or (obj < best["obj"] - 1e-9):
                    best = {"d2": d2, "d3": d3, "sn": sn, "obj": obj}

    if best is None:
        return {"status": "NO_SOLUTION", "SN_best": best_sn}

    return {
        "status": "OK",
        "D1_in": d1_fixed_in,
        "D2_in": best["d2"],
        "D3_in": best["d3"],
        "D1_cm": _in_to_cm(d1_fixed_in),
        "D2_cm": _in_to_cm(best["d2"]),
        "D3_cm": _in_to_cm(best["d3"]),
        "SN_provided": best["sn"],
    }


def minimum_thicknesses_by_w18(w18: float) -> dict:
    """Tabla 7-2 de mínimos sugeridos (AASHTO 1993), en cm e in."""
    if w18 < 50_000:
        asphalt_cm, base_cm, label = 3.0, 10.0, "< 50,000"
    elif w18 < 150_000:
        asphalt_cm, base_cm, label = 5.0, 10.0, "50,000 - 150,000"
    elif w18 < 500_000:
        asphalt_cm, base_cm, label = 6.5, 10.0, "150,000 - 500,000"
    elif w18 < 2_000_000:
        asphalt_cm, base_cm, label = 7.5, 15.0, "500,000 - 2,000,000"
    elif w18 <= 7_000_000:
        asphalt_cm, base_cm, label = 9.0, 15.0, "2,000,000 - 7,000,000"
    else:
        asphalt_cm, base_cm, label = 10.0, 15.0, "> 7,000,000"

    return {
        "range_label": label,
        "D1_min_cm": asphalt_cm,
        "D2_min_cm": base_cm,
        "D1_min_in": _cm_to_in(asphalt_cm),
        "D2_min_in": _cm_to_in(base_cm),
    }


def apply_minimums(rec: dict, w18: float):
    mins = minimum_thicknesses_by_w18(w18)
    d1_min = mins["D1_min_in"]
    d2_min = mins["D2_min_in"]

    d1_adj = max(rec["D1_in"], d1_min)
    d2_adj = max(rec["D2_in"], d2_min)

    return {
        "D1_in": d1_adj,
        "D2_in": d2_adj,
        "D3_in": rec["D3_in"],
        "D1_cm": _in_to_cm(d1_adj),
        "D2_cm": _in_to_cm(d2_adj),
        "D3_cm": rec["D3_cm"],
        "minimum_table": mins,
        "minimums_govern": (d1_adj > rec["D1_in"] + 1e-9) or (d2_adj > rec["D2_in"] + 1e-9),
    }
