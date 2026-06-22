import os, requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
FOOTBALL_KEY = os.getenv("FOOTBALL_DATA_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

WC_VENUES = {
    "AT&T Stadium": {"lat": 32.75, "lon": -97.09, "city": "Dallas"},
    "MetLife Stadium": {"lat": 40.81, "lon": -74.07, "city": "New Jersey"},
    "SoFi Stadium": {"lat": 33.95, "lon": -118.34, "city": "Los Angeles"},
    "Lincoln Financial": {"lat": 39.90, "lon": -75.17, "city": "Philadelphia"},
    "Levi's Stadium": {"lat": 37.40, "lon": -121.97, "city": "Santa Clara"},
    "NRG Stadium": {"lat": 29.68, "lon": -95.41, "city": "Houston"},
    "Arrowhead": {"lat": 39.05, "lon": -94.48, "city": "Kansas City"},
    "Lumen Field": {"lat": 47.60, "lon": -122.33, "city": "Seattle"},
    "Hard Rock": {"lat": 25.96, "lon": -80.24, "city": "Miami"},
    "BMO Field": {"lat": 43.63, "lon": -79.41, "city": "Toronto"},
    "BC Place": {"lat": 49.27, "lon": -123.11, "city": "Vancouver"},
    "Estadio Azteca": {"lat": 19.30, "lon": -99.15, "city": "Mexico City"},
    "Estadio BBVA": {"lat": 25.66, "lon": -100.24, "city": "Monterrey"},
    "Akron": {"lat": 20.60, "lon": -103.46, "city": "Guadalajara"},
    "default": {"lat": 29.68, "lon": -95.41, "city": "Houston"},
}

def get_todays_matches():
    """Obtiene partidos WC2026 de hoy desde football-data.org"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": FOOTBALL_KEY}
    params = {"dateFrom": today, "dateTo": today, "status": "SCHEDULED,TIMED,IN_PLAY"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        matches = []
        for m in data.get("matches", []):
            matches.append({
                "id": m["id"],
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "utcDate": m["utcDate"],
                "group": m.get("group", ""),
                "stage": m["stage"],
            })
        return matches
    except Exception as e:
        print(f"[football-data] Error: {e}")
        return []

def get_odds(home_team, away_team):
    """Obtiene odds H2H para un partido desde The Odds API"""
    url = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup_2026/odds/"
    params = {
        "apiKey": ODDS_KEY,
        "regions": "us,uk",
        "markets": "h2h",
        "oddsFormat": "american",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        games = r.json()
        for g in games:
            ht = g.get("home_team", "").lower()
            at = g.get("away_team", "").lower()
            h_clean = home_team.lower().split()[0]
            a_clean = away_team.lower().split()[0]
            if h_clean in ht or a_clean in at:
                for bk in g.get("bookmakers", []):
                    for mkt in bk.get("markets", []):
                        if mkt["key"] == "h2h":
                            odds_map = {o["name"].lower(): o["price"] for o in mkt["outcomes"]}
                            h_odds = odds_map.get(ht, -110)
                            a_odds = odds_map.get(at, +110)
                            d_odds = odds_map.get("draw", +250)
                            return {"home": h_odds, "draw": d_odds, "away": a_odds}
        return {"home": -110, "draw": +250, "away": +110}
    except Exception as e:
        print(f"[odds-api] Error: {e}")
        return {"home": -110, "draw": +250, "away": +110}

def get_weather(venue_keyword="default"):
    """Obtiene temperatura actual del estadio via Open-Meteo (sin key)"""
    venue = None
    for k, v in WC_VENUES.items():
        if venue_keyword.lower() in k.lower():
            venue = v
            break
    if not venue:
        venue = WC_VENUES["default"]
    url = (f"https://api.open-meteo.com/v1/forecast"
           f"?latitude={venue['lat']}&longitude={venue['lon']}"
           f"&current=temperature_2m,wind_speed_10m"
           f"&temperature_unit=celsius")
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        temp = data["current"]["temperature_2m"]
        return {"city": venue["city"], "temp_c": temp}
    except Exception as e:
        print(f"[open-meteo] Error: {e}")
        return {"city": venue.get("city", "?"), "temp_c": 22}

def get_recent_results(team_name, n=3):
    """Obtiene últimos N resultados de un equipo en WC2026"""
    url = f"https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": FOOTBALL_KEY}
    params = {"status": "FINISHED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        matches = r.json().get("matches", [])
        team_matches = []
        for m in matches:
            ht = m["homeTeam"]["name"]
            at = m["awayTeam"]["name"]
            t_clean = team_name.lower().split()[0]
            if t_clean in ht.lower() or t_clean in at.lower():
                hg = m["score"]["fullTime"]["home"]
                ag = m["score"]["fullTime"]["away"]
                if hg is not None:
                    is_home = t_clean in ht.lower()
                    gf = hg if is_home else ag
                    ga = ag if is_home else hg
                    team_matches.append({"gf": gf, "ga": ga, "date": m["utcDate"]})
        return team_matches[-n:]
    except Exception as e:
        print(f"[football-data results] Error: {e}")
        return []
