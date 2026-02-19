import math


def _inv_norm_cdf(p: float) -> float:
    """
    Inversa aproximada de la normal estándar (Acklam).
    p en (0,1). Retorna z tal que Phi(z)=p.
    """
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p debe estar entre 0 y 1 (exclusivo)")

    # Coeficientes Acklam
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]

    plow = 0.02425
    phigh = 1 - plow

    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
               ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)

    q = p - 0.5
    r = q*q
    return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q / \
           (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)


def _aashto_log10_w18(sn: float, zr: float, so: float, dpsi: float, mr_psi: float) -> float:
    """
    Retorna log10(W18) según AASHTO 93 flexible para SN dado.
    """
    if sn <= 0:
        return -1e9
    if mr_psi <= 0:
        raise ValueError("Mr debe ser > 0")
    if so <= 0:
        raise ValueError("So debe ser > 0")
    if dpsi <= 0:
        raise ValueError("ΔPSI debe ser > 0")

    term1 = zr * so
    term2 = 9.36 * math.log10(sn + 1.0) - 0.20
    term3_num = math.log10(dpsi / (4.2 - 1.5))
    term3_den = 0.40 + (1094.0 / ((sn + 1.0) ** 5.19))
    term3 = term3_num / term3_den
    term4 = 2.32 * math.log10(mr_psi) - 8.07

    return term1 + term2 + term3 + term4


def solve_sn_required(w18: float, reliability_pct: float, so: float, pi: float, pt: float, mr_mpa: float):
    """
    Resuelve SN requerido por bisección.
    mr_mpa se convierte a psi internamente.
    Retorna (SN, Zr)
    """
    if w18 <= 0:
        raise ValueError("W18 debe ser > 0")
    if not (50 <= reliability_pct < 99.99):
        raise ValueError("R recomendado entre 50 y < 99.99 (%)")
    if pi <= pt:
        raise ValueError("Pi debe ser > Pt")

    dpsi = pi - pt
    mr_psi = mr_mpa * 145.03773773

    # Zr: confiabilidad R% => prob de no fallar; AASHTO usa Zr negativo para altas confiabilidades.
    # Si R=95%, Phi(z)=1-R => z=Phi^-1(0.05)=-1.645
    p = 1.0 - (reliability_pct / 100.0)
    zr = _inv_norm_cdf(p)

    target = math.log10(w18)

    # Bisección en SN
    lo, hi = 0.1, 10.0
    f_lo = _aashto_log10_w18(lo, zr, so, dpsi, mr_psi) - target
    f_hi = _aashto_log10_w18(hi, zr, so, dpsi, mr_psi) - target

    # expandir hi si hace falta
    it = 0
    while f_hi < 0 and it < 40:
        hi *= 1.5
        f_hi = _aashto_log10_w18(hi, zr, so, dpsi, mr_psi) - target
        it += 1

    if f_lo > 0:
        # ya con SN muy pequeño excede; algo raro en entradas
        return lo, zr
    if f_hi < 0:
        raise ValueError("No se pudo encerrar la raíz. Revisa entradas (W18 muy alto o parámetros).")

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = _aashto_log10_w18(mid, zr, so, dpsi, mr_psi) - target
        if abs(f_mid) < 1e-6:
            return mid, zr
        if f_mid > 0:
            hi = mid
        else:
            lo = mid

    return 0.5 * (lo + hi), zr
