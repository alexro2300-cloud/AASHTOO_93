def _cm_to_in(cm: float) -> float:
    return cm / 2.54


def _in_to_cm(inches: float) -> float:
    return inches * 2.54


def sn_provided(a1, a2, a3, m2, m3, d1_in, d2_in, d3_in) -> float:
    return a1*d1_in + a2*m2*d2_in + a3*m3*d3_in


def recommend_thicknesses(
    sn_required: float,
    a1: float, a2: float, a3: float,
    m2: float, m3: float,
    step_in: float,
    d1_fixed_cm: float,
    d2_min_cm: float, d2_max_cm: float,
    d3_min_cm: float, d3_max_cm: float
):
    """
    MVP: D1 fijo; busca el menor (D2,D3) en una malla que cumpla SN.
    Criterio: minimizar (D2 + D3). Paso en pulgadas.
    """
    if sn_required <= 0:
        raise ValueError("SN requerido debe ser > 0")
    if step_in <= 0:
        raise ValueError("step_in debe ser > 0")

    d1_in = _cm_to_in(d1_fixed_cm)

    d2_min_in = _cm_to_in(d2_min_cm); d2_max_in = _cm_to_in(d2_max_cm)
    d3_min_in = _cm_to_in(d3_min_cm); d3_max_in = _cm_to_in(d3_max_cm)

    best = None
    best_sn = -1e9

    # Itera D2 y D3 en malla
    d2 = d2_min_in
    while d2 <= d2_max_in + 1e-9:
        d3 = d3_min_in
        while d3 <= d3_max_in + 1e-9:
            sn = sn_provided(a1, a2, a3, m2, m3, d1_in, d2, d3)
            if sn > best_sn:
                best_sn = sn
            if sn >= sn_required:
                obj = d2 + d3
                if (best is None) or (obj < best["obj"] - 1e-9):
                    best = {"d2": d2, "d3": d3, "sn": sn, "obj": obj}
            d3 += step_in
        d2 += step_in

    if best is None:
        return {"status": "NO_SOLUTION", "SN_best": best_sn}

    return {
        "status": "OK",
        "D1_cm": d1_fixed_cm,
        "D2_cm": _in_to_cm(best["d2"]),
        "D3_cm": _in_to_cm(best["d3"]),
        "SN_provided": best["sn"]
    }
