"""Interfaz web (Flask) para el predictor Mundial 2026."""
from flask import Flask, render_template, request
from model import build_lambda, simulate, devig, XG_DATABASE, ELO
from fetch_data import get_odds, get_weather, WC_VENUES

app = Flask(__name__)

# Lista ordenada de equipos disponibles (los que tienen datos cargados)
TEAMS = sorted(set(list(XG_DATABASE.keys()) + list(ELO.keys())))
VENUES = [v for v in WC_VENUES.keys() if v != "default"]


def analizar(home, away, venue, use_live):
    """Corre el modelo para un partido y devuelve un dict listo para el template."""
    # Odds y clima: en vivo (APIs) o valores por defecto
    if use_live:
        odds = get_odds(home, away)
        weather = get_weather(venue or "default")
    else:
        odds = {"home": -110, "draw": 250, "away": 110}
        v = WC_VENUES.get(venue, WC_VENUES["default"])
        weather = {"city": v["city"], "temp_c": 22}

    temp = weather["temp_c"]
    lh, la, rho = build_lambda(home, away, odds, temp_c=temp)
    r = simulate(lh, la, rho)

    ph_m, pd_m, pa_m = devig(odds["home"], odds["draw"], odds["away"])
    eh = r["pw"] - ph_m
    ed = r["pd"] - pd_m
    ea = r["pl"] - pa_m
    converge = abs(eh) < 0.08 and abs(ea) < 0.08

    mx = max(r["pw"], r["pd"], r["pl"])
    if r["pw"] > 0.55:
        pick = f"{home} gana"
    elif r["pl"] > 0.55:
        pick = f"{away} gana"
    elif r["pd"] > 0.30:
        pick = "Empate"
    else:
        pick = f"Parejo (max {mx*100:.0f}%)"

    if mx > 0.65 and converge:
        conf = ("ALTA", "alta")
    elif mx > 0.50 and converge:
        conf = ("MEDIA", "media")
    else:
        conf = ("BAJA", "baja")

    top = [{"score": f"{s[0]}-{s[1]}", "prob": p * 100} for s, p in r["top"][:6]]
    top_s, top_p = r["top"][0]

    return {
        "home": home, "away": away,
        "city": weather["city"], "temp": temp,
        "odds": odds,
        "lh": r["lh"], "la": r["la"], "rho": r["rho"],
        "xg_total": r["lh"] + r["la"],
        "pw": r["pw"] * 100, "pd": r["pd"] * 100, "pl": r["pl"] * 100,
        "mkt_h": ph_m * 100, "mkt_d": pd_m * 100, "mkt_a": pa_m * 100,
        "eh": eh * 100, "ed": ed * 100, "ea": ea * 100,
        "o25": r["o25"] * 100, "u25": r["u25"] * 100,
        "btts": r["btts"] * 100, "cs_h": r["cs_h"] * 100,
        "top": top,
        "pick": pick,
        "score": f"{top_s[0]}-{top_s[1]}", "score_prob": top_p * 100,
        "conf": conf[0], "conf_class": conf[1],
        "converge": converge,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    home = request.form.get("home", "")
    away = request.form.get("away", "")
    venue = request.form.get("venue", "")
    use_live = request.form.get("use_live") == "on"

    if request.method == "POST":
        if not home or not away:
            error = "Elegí equipo local y visitante."
        elif home == away:
            error = "El local y el visitante no pueden ser el mismo equipo."
        else:
            result = analizar(home, away, venue, use_live)

    return render_template(
        "index.html",
        teams=TEAMS, venues=VENUES,
        result=result, error=error,
        home=home, away=away, venue=venue, use_live=use_live,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
