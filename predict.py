import sys
from fetch_data import get_todays_matches, get_odds, get_weather
from model import build_lambda, simulate, devig, XG_DATABASE

SEPARADOR = "─" * 64

def conf(pw, pd, pl, converge):
    mx = max(pw, pd, pl)
    if mx > 0.65 and converge: return "🟢 ALTA"
    if mx > 0.50 and converge: return "🟡 MEDIA"
    return "🔴 BAJA"

def run(matches=None, venue="default"):
    print("=" * 64)
    print("  ⚽ MODELO MUNDIAL 2026 — Dixon-Coles + Monte Carlo (300k)")
    print("  μ WC2026 = 1.553 | Datos: football-data.org + the-odds-api")
    print("=" * 64)

    # Si no se pasan partidos, buscar los de hoy
    if not matches:
        print("\n🔍 Buscando partidos de hoy en football-data.org...")
        matches = get_todays_matches()
        if not matches:
            print("⚠️  No se encontraron partidos hoy. Probá pasar partidos manualmente.")
            print('   Ejemplo: python predict.py "Argentina" "Austria" "AT&T Stadium"')
            return

    print(f"\n  {len(matches)} partido(s) encontrado(s)\n")

    results = []
    for m in matches:
        home = m["home"]
        away = m["away"]
        venue_kw = m.get("venue", venue)

        print(f"  Procesando: {home} vs {away}...")

        # Odds reales
        odds = get_odds(home, away)

        # Clima
        weather = get_weather(venue_kw)
        temp = weather["temp_c"]

        # Construir lambda
        lh, la, rho = build_lambda(home, away, odds, temp_c=temp)

        # Simular
        r = simulate(lh, la, rho)

        # Edge vs mercado
        ph_m, pd_m, pa_m = devig(odds["home"], odds["draw"], odds["away"])
        eh = r["pw"] - ph_m
        ed = r["pd"] - pd_m
        ea = r["pl"] - pa_m
        converge = abs(eh) < 0.08 and abs(ea) < 0.08

        # Pick
        mx = max(r["pw"], r["pd"], r["pl"])
        if r["pw"] > 0.55:   pick = f"{home} gana"
        elif r["pl"] > 0.55: pick = f"{away} gana"
        elif r["pd"] > 0.30: pick = "Empate"
        else:                 pick = f"⚠️ PAREJO (max {mx*100:.0f}%)"

        top_s, top_p = r["top"][0]
        results.append(dict(home=home, away=away, r=r, odds=odds,
                            temp=temp, city=weather["city"],
                            eh=eh, ed=ed, ea=ea, pick=pick,
                            converge=converge, top_s=top_s, top_p=top_p))

    # OUTPUT
    for res in results:
        r = res["r"]
        odds = res["odds"]
        ph_m, pd_m, pa_m = devig(odds["home"], odds["draw"], odds["away"])
        c = conf(r["pw"], r["pd"], r["pl"], res["converge"])
        cal = "✅" if res["converge"] else f"⚠️ diverge"

        print(f"\n{SEPARADOR}")
        print(f"  ⚽ {res['home']} vs {res['away']}")
        print(f"  📍 {res['city']} | 🌡️  {res['temp']:.1f}°C")
        print(f"  Odds: {odds['home']:+d} / Draw {odds['draw']:+d} / {odds['away']:+d}")
        print(f"  λ: {r['lh']:.2f} vs {r['la']:.2f} | rho={r['rho']} | xG total={r['lh']+r['la']:.2f}")
        print(f"\n  🎲 1X2:")
        print(f"    {res['home']:<20} {r['pw']*100:5.1f}%  mkt={ph_m*100:.1f}%  edge={res['eh']*100:+.1f}%")
        print(f"    {'Empate':<20} {r['pd']*100:5.1f}%  mkt={pd_m*100:.1f}%  edge={res['ed']*100:+.1f}%")
        print(f"    {res['away']:<20} {r['pl']*100:5.1f}%  mkt={pa_m*100:.1f}%  edge={res['ea']*100:+.1f}%")
        print(f"    Calibración vs mercado: {cal}")
        print(f"\n  📊 Goles: O2.5={r['o25']*100:.0f}%  U2.5={r['u25']*100:.0f}%  BTTS={r['btts']*100:.0f}%  CS={r['cs_h']*100:.0f}%")
        print(f"\n  🏆 Top marcadores:")
        for i, (sc, prob) in enumerate(r["top"][:6]):
            s = "⭐" if i == 0 else f"  {i+1}."
            print(f"    {s} {sc[0]}-{sc[1]}  {prob*100:.2f}%")
        print(f"\n  🔮 Confianza: {c}")
        print(f"  📋 Pick: {res['pick']}  |  Score: {res['top_s'][0]}-{res['top_s'][1]} ({res['top_p']*100:.1f}%)")

    print(f"\n{'='*64}")
    print("  RESUMEN")
    print(f"{'='*64}")
    for res in results:
        print(f"  {res['home']:<18} vs {res['away']:<18} → {res['pick']:<22} {res['top_s'][0]}-{res['top_s'][1]}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        # Modo manual: python predict.py "Argentina" "Austria" "AT&T Stadium"
        home = sys.argv[1]
        away = sys.argv[2]
        venue = sys.argv[3] if len(sys.argv) > 3 else "default"
        run(matches=[{"home": home, "away": away, "venue": venue}], venue=venue)
    else:
        # Modo automático: busca partidos de hoy
        run()
