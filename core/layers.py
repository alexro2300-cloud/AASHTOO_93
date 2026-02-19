import math


def _cm_to_in(cm: float) -> float:
    return cm / 2.54


def _in_to_cm(inches: float) -> float:
    return inches * 2.54


def sn_provided(a1, a2, a3, m2, m3, d1_in, d2_in, d3_in) -> float:
    return a1 * d1_in + a2 * m2 * d2_in + a3 * m3 * d3_in


def round_half_nearest(value_in: float) -> float:
    return round(value_in * 2.0) / 2.0


def round_half_up(value_in: float) -> float:
    if value_in <= 0:
        return 0.0
    return math.ceil(value_in * 2.0 - 1e-12) / 2.0


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


def design_thicknesses_sequential(sn1_target, sn2_target, sn3_target, a1, a2, a3, m2, m3):
    """
    Metodología secuencial solicitada por el usuario:
    1) D1=SN1/a1 (redondeo 0.5 in más cercana)
    2) D2=(SN2-SN1*)/(a2*m2) (redondeo 0.5 in hacia arriba)
    3) D3=(SN3-(SN1*+SN2*))/(a3*m3) (redondeo 0.5 in hacia arriba)
    """
    if a1 <= 0 or a2 <= 0 or a3 <= 0 or m2 <= 0 or m3 <= 0:
        raise ValueError("a1, a2, a3, m2 y m3 deben ser > 0")
    if sn1_target <= 0 or sn2_target <= 0 or sn3_target <= 0:
        raise ValueError("SN1, SN2 y SN3 deben ser > 0")
    if not (sn1_target <= sn2_target <= sn3_target):
        raise ValueError("Debe cumplirse SN1 <= SN2 <= SN3")

    d1_raw = sn1_target / a1
    d1_round = round_half_nearest(d1_raw)
    sn1_star = d1_round * a1

    d2_raw = (sn2_target - sn1_star) / (a2 * m2)
    d2_round = round_half_up(d2_raw)
    sn2_star = d2_round * a2 * m2

    d3_raw = (sn3_target - (sn1_star + sn2_star)) / (a3 * m3)
    d3_round = round_half_up(d3_raw)
    sn3_star = d3_round * a3 * m3

    sn_sum = sn1_star + sn2_star + sn3_star
    return {
        "SN1_target": sn1_target,
        "SN2_target": sn2_target,
        "SN3_target": sn3_target,
        "D1_raw_in": d1_raw,
        "D2_raw_in": d2_raw,
        "D3_raw_in": d3_raw,
        "D1_in": d1_round,
        "D2_in": d2_round,
        "D3_in": d3_round,
        "D1_cm": _in_to_cm(d1_round),
        "D2_cm": _in_to_cm(d2_round),
        "D3_cm": _in_to_cm(d3_round),
        "SN1_star": sn1_star,
        "SN2_star": sn2_star,
        "SN3_star": sn3_star,
        "SN_sum": sn_sum,
        "criterion_user_lt_sn3": sn_sum < sn3_target,
        "criterion_meets_or_exceeds": sn_sum >= sn3_target,
    }


def apply_minimums_sequential(calc_result: dict, w18: float, a1, a2, a3, m2, m3, sn3_target: float):
    """
    Ajusta carpeta/base por mínimos Tabla 7-2 y recalcula subbase.
    """
    mins = minimum_thicknesses_by_w18(w18)

    d1_min_round = round_half_up(mins["D1_min_in"])
    d2_min_round = round_half_up(mins["D2_min_in"])

    d1_adj = max(calc_result["D1_in"], d1_min_round)
    d2_adj = max(calc_result["D2_in"], d2_min_round)

    sn1_star = d1_adj * a1
    sn2_star = d2_adj * a2 * m2

    d3_raw = (sn3_target - (sn1_star + sn2_star)) / (a3 * m3)
    d3_adj = round_half_up(d3_raw)
    sn3_star = d3_adj * a3 * m3

    sn_sum = sn1_star + sn2_star + sn3_star

    return {
        "minimum_table": mins,
        "D1_in": d1_adj,
        "D2_in": d2_adj,
        "D3_in": d3_adj,
        "D1_cm": _in_to_cm(d1_adj),
        "D2_cm": _in_to_cm(d2_adj),
        "D3_cm": _in_to_cm(d3_adj),
        "D3_raw_in": d3_raw,
        "SN1_star": sn1_star,
        "SN2_star": sn2_star,
        "SN3_star": sn3_star,
        "SN_sum": sn_sum,
        "minimums_govern": (d1_adj > calc_result["D1_in"] + 1e-9) or (d2_adj > calc_result["D2_in"] + 1e-9),
        "criterion_user_lt_sn3": sn_sum < sn3_target,
        "criterion_meets_or_exceeds": sn_sum >= sn3_target,
    }
