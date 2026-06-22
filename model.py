import numpy as np
from scipy.stats import poisson
from collections import Counter

# μ calibrado con datos reales WC2026 (actualizar después de cada jornada)
MU_WC2026 = 1.553

# xG MD1 reales por equipo — actualizar con cada jornada
XG_DATABASE = {
    "Argentina": {"xg_for": 2.20, "xg_against": 0.40, "pts": 3, "gf": 3, "ga": 0},
    "Austria": {"xg_for": 2.00, "xg_against": 0.70, "pts": 3, "gf": 3, "ga": 1},
    "Algeria": {"xg_for": 0.92, "xg_against": 2.20, "pts": 0, "gf": 0, "ga": 3},
    "Jordan": {"xg_for": 0.70, "xg_against": 2.00, "pts": 0, "gf": 1, "ga": 3},
    "France": {"xg_for": 2.10, "xg_against": 0.80, "pts": 3, "gf": 3, "ga": 1},
    "Iraq": {"xg_for": 0.60, "xg_against": 2.50, "pts": 0, "gf": 1, "ga": 4},
    "Norway": {"xg_for": 2.50, "xg_against": 1.00, "pts": 3, "gf": 4, "ga": 1},
    "Senegal": {"xg_for": 0.80, "xg_against": 2.10, "pts": 0, "gf": 1, "ga": 3},
    "Spain": {"xg_for": 2.29, "xg_against": 0.30, "pts": 1, "gf": 0, "ga": 0},
    "Saudi Arabia": {"xg_for": 0.99, "xg_against": 1.54, "pts": 1, "gf": 1, "ga": 1},
    "Uruguay": {"xg_for": 1.54, "xg_against": 0.99, "pts": 1, "gf": 1, "ga": 1},
    "Cape Verde": {"xg_for": 0.30, "xg_against": 2.29, "pts": 1, "gf": 0, "ga": 0},
    "Belgium": {"xg_for": 1.35, "xg_against": 1.08, "pts": 1, "gf": 1, "ga": 1},
    "Egypt": {"xg_for": 1.08, "xg_against": 1.35, "pts": 1, "gf": 1, "ga": 1},
    "Iran": {"xg_for": 1.50, "xg_against": 0.90, "pts": 1, "gf": 2, "ga": 2},
    "New Zealand": {"xg_for": 0.90, "xg_against": 1.50, "pts": 1, "gf": 2, "ga": 2},
    "Germany": {"xg_for": 4.22, "xg_against": 0.41, "pts": 3, "gf": 7, "ga": 1},
    "Ivory Coast": {"xg_for": 1.68, "xg_against": 1.03, "pts": 3, "gf": 1, "ga": 0},
    "Ecuador": {"xg_for": 1.03, "xg_against": 1.68, "pts": 0, "gf": 0, "ga": 1},
    "Curacao": {"xg_for": 0.41, "xg_against": 4.22, "pts": 0, "gf": 1, "ga": 7},
    "Netherlands": {"xg_for": 0.78, "xg_against": 0.59, "pts": 1, "gf": 2, "ga": 2},
    "Japan": {"xg_for": 0.59, "xg_against": 0.78, "pts": 1, "gf": 2, "ga": 2},
    "Sweden": {"xg_for": 1.36, "xg_against": 0.28, "pts": 3, "gf": 5, "ga": 1},
    "Tunisia": {"xg_for": 0.28, "xg_against": 1.36, "pts": 0, "gf": 1, "ga": 5},
    "Portugal": {"xg_for": 2.80, "xg_against": 0.50, "pts": 1, "gf": 1, "ga": 1},
    "DR Congo": {"xg_for": 0.50, "xg_against": 2.80, "pts": 1, "gf": 1, "ga": 1},
    "Colombia": {"xg_for": 2.20, "xg_against": 0.70, "pts": 3, "gf": 3, "ga": 1},
    "England": {"xg_for": 2.30, "xg_against": 1.20, "pts": 3, "gf": 4, "ga": 2},
    "Croatia": {"xg_for": 1.20, "xg_against": 2.30, "pts": 0, "gf": 2, "ga": 4},
    "Brazil": {"xg_for": 1.23, "xg_against": 1.53, "pts": 1, "gf": 1, "ga": 1},
    "Morocco": {"xg_for": 1.53, "xg_against": 1.23, "pts": 1, "gf": 1, "ga": 1},
    "Mexico": {"xg_for": 1.41, "xg_against": 0.07, "pts": 3, "gf": 2, "ga": 0},
    "South Korea": {"xg_for": 1.84, "xg_against": 0.81, "pts": 3, "gf": 2, "ga": 1},
    "USA": {"xg_for": 1.35, "xg_against": 0.47, "pts": 3, "gf": 4, "ga": 1},
    "Australia": {"xg_for": 0.77, "xg_against": 1.33, "pts": 3, "gf": 2, "ga": 0},
    "Switzerland": {"xg_for": 3.24, "xg_against": 0.76, "pts": 1, "gf": 1, "ga": 1},
    "Qatar": {"xg_for": 0.76, "xg_against": 3.24, "pts": 1, "gf": 1, "ga": 1},
    "Canada": {"xg_for": 1.25, "xg_against": 0.98, "pts": 1, "gf": 1, "ga": 1},
    "Scotland": {"xg_for": 1.05, "xg_against": 1.21, "pts": 3, "gf": 1, "ga": 0},
    "Haiti": {"xg_for": 1.21, "xg_against": 1.05, "pts": 0, "gf": 0, "ga": 1},
}

ELO = {
    "Argentina": 1950, "France": 1980, "Brazil": 1950, "Spain": 1920,
    "Germany": 1930, "England": 1890, "Netherlands": 1870, "Portugal": 1860,
    "Belgium": 1840, "Norway": 1800, "Mexico": 1800, "USA": 1750,
    "Morocco": 1760, "Uruguay": 1800, "Switzerland": 1781, "Colombia": 1800,
    "Japan": 1760, "South Korea": 1754, "Australia": 1680, "Sweden": 1780,
    "Austria": 1820, "Ivory Coast": 1760, "Ecuador": 1710, "Senegal": 1780,
    "Canada": 1741, "Scotland": 1650, "Croatia": 1820, "Qatar": 1591,
    "Algeria": 1750, "Iraq": 1480, "Tunisia": 1600, "Iran": 1720,
    "Saudi Arabia": 1680, "Egypt": 1700, "Jordan": 1500, "Cape Verde": 1580,
    "New Zealand": 1560, "Haiti": 1450, "Curacao": 1430, "DR Congo": 1526,
    "Bosnia": 1589, "Paraguay": 1660, "Turkey": 1740, "South Africa": 1526,
    "Ghana": 1650, "Panama": 1580, "Uzbekistan": 1620,
}

def dixon_coles(i, j, lam_h, lam_a, rho):
    if i == 0 and j == 0: return 1 - lam_h * lam_a * rho
    if i == 0 and j == 1: return 1 + lam_h * rho
    if i == 1 and j == 0: return 1 + lam_a * rho
    if i == 1 and j == 1: return 1 - rho
    return 1.0

def devig(oh, od, oa):
    def p(o): return abs(o)/(abs(o)+100) if o < 0 else 100/(o+100)
    ph, pd, pa = p(oh), p(od), p(oa)
    t = ph + pd + pa
    return ph/t, pd/t, pa/t

def build_lambda(home, away, odds, home_adv=1.0, temp_c=22,
                 susp_h=1.0, susp_a=1.0, motiv_h=1.0, motiv_a=1.0,
                 shrinkage=0.65):
    db = XG_DATABASE
    xg_h = db.get(home, {}).get("xg_for", MU_WC2026)
    xg_a = db.get(away, {}).get("xg_for", MU_WC2026)
    pts_h = db.get(home, {}).get("pts", 1)
    pts_a = db.get(away, {}).get("pts", 1)

    # Shrinkage hacia μ del torneo
    lh = shrinkage * xg_h + (1 - shrinkage) * MU_WC2026
    la = shrinkage * xg_a + (1 - shrinkage) * MU_WC2026

    # ELO
    elo_h = ELO.get(home, 1650)
    elo_a = ELO.get(away, 1650)
    diff = elo_h - elo_a
    lh *= max(0.78, min(1.22, 1 + 0.00028 * diff))
    la *= max(0.78, min(1.22, 1 - 0.00028 * diff))

    # Motivación automática por pts
    if pts_h == 0: lh *= 1.15
    elif pts_h >= 3: lh *= 0.92
    if pts_a == 0: la *= 1.15
    elif pts_a >= 3: la *= 0.92

    # Ajustes externos
    lh *= home_adv * susp_h * motiv_h
    la *= susp_a * motiv_a

    # Temperatura — calor reduce pressing
    if temp_c > 32:
        factor = max(0.85, 1 - (temp_c - 32) * 0.008)
        lh *= factor; la *= factor

    # Prior bayesiano mercado (35%)
    ph_m, _, pa_m = devig(odds["home"], odds["draw"], odds["away"])
    ratio = ph_m / max(pa_m, 0.01)
    lh_mkt = MU_WC2026 * (ratio ** 0.5) * 0.92
    la_mkt = MU_WC2026 / (ratio ** 0.5) * 0.92

    lh_f = 0.65 * lh + 0.35 * lh_mkt
    la_f = 0.65 * la + 0.35 * la_mkt

    # rho dinámico: partido trabado vs abierto
    xg_total = lh_f + la_f
    rho = -0.07 if xg_total < 2.5 else (-0.05 if xg_total < 3.5 else -0.03)

    return max(0.30, min(4.0, lh_f)), max(0.30, min(4.0, la_f)), rho

def simulate(lh, la, rho, N=300000, max_g=8):
    np.random.seed(2026)
    P = np.zeros((max_g+1, max_g+1))
    for i in range(max_g+1):
        for j in range(max_g+1):
            p = poisson.pmf(i, lh) * poisson.pmf(j, la)
            P[i, j] = p * max(dixon_coles(i, j, lh, la, rho), 0)
    P /= P.sum()
    flat = P.flatten()
    idx = np.random.choice(len(flat), size=N, p=flat)
    hg = idx // (max_g+1); ag = idx % (max_g+1)
    pw = float(np.mean(hg > ag))
    pd = float(np.mean(hg == ag))
    pl = float(np.mean(hg < ag))
    o25 = float(np.mean(hg+ag > 2))
    btts = float(np.mean((hg>0)&(ag>0)))
    cs_h = float(np.mean(ag == 0))
    sc = Counter(zip(hg.tolist(), ag.tolist()))
    top = [(s, c/N) for s, c in sorted(sc.items(), key=lambda x:-x[1])[:8]]
    return dict(pw=pw, pd=pd, pl=pl, o25=o25, u25=1-o25,
                btts=btts, cs_h=cs_h, top=top, lh=lh, la=la, rho=rho)
