import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ========== SETTINGS ==========
API_URL = "https://v3.football.api-sports.io"
API_KEY = st.secrets["API_KEY"]  # Το βάζεις στο Streamlit secrets

# ========== FUNCTIONS ==========

def get_fixtures():
    headers = {"x-apisports-key": API_KEY}
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"{API_URL}/fixtures?date={today}"
    r = requests.get(url, headers=headers)
    data = r.json()
    return data.get("response", [])

def get_odds(fixture_id):
    headers = {"x-apisports-key": API_KEY}
    url = f"{API_URL}/odds?fixture={fixture_id}"
    r = requests.get(url, headers=headers)
    data = r.json()
    return data.get("response", [])

def implied_prob(decimal_odd):
    try:
        return 1 / decimal_odd if decimal_odd > 0 else 0
    except:
        return 0

def simple_model(home_team, away_team):
    # Dummy πιθανότητες: Home 50%, Draw 25%, Away 25%
    return {"Home": 0.5, "Draw": 0.25, "Away": 0.25}

# ========== UI ==========

st.title("Football Value Bets Finder")
st.write("Απλό εργαλείο για εύρεση Value Bets από το API-Football.")

fixtures = get_fixtures()

if not fixtures:
    st.warning("Δεν βρέθηκαν αγώνες για σήμερα.")
else:
    rows = []
    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]

        odds_data = get_odds(fixture_id)
        if not odds_data:
            continue

        # Παίρνουμε την πρώτη διαθέσιμη αγορά 1X2
        for bookmaker in odds_data:
            bets = bookmaker.get("bookmakers", [])
            for b in bets:
                for bet in b.get("bets", []):
                    if bet["name"] == "Match Winner":
                        for val in bet["values"]:
                            market = val["value"]
                            odd = float(val["odd"])
                            imp = implied_prob(odd)
                            model_probs = simple_model(home, away)
                            edge = model_probs.get(market, 0) - imp
                            rows.append({
                                "Match": f"{home} vs {away}",
                                "Market": market,
                                "Odd": odd,
                                "ImpliedProb": round(imp, 3),
                                "ModelProb": model_probs.get(market, 0),
                                "Edge": round(edge, 3)
                            })

    if rows:
        df = pd.DataFrame(rows)
        value_bets = df[df["Edge"] > 0.05]
        st.subheader("Value Bets (Edge > 5%)")
        st.dataframe(value_bets)
    else:
        st.info("Δεν βρέθηκαν αποδόσεις για τους σημερινούς αγώνες.")
