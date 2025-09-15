import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ========== SETTINGS ==========
API_URL = "https://v3.football.api-sports.io"
API_KEY = st.secrets["API_KEY"]  # Βάλε το API Key σου στα Streamlit secrets

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
st.write("Εμφανίζει πιθανά Value Bets για σημερινούς αγώνες.")

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
        df = df.sort_values(by="Edge", ascending=False)
        top_value_bets = df[df["Edge"] > 0.05].head(5)

        st.subheader("Top 5 Value Bets (Edge > 5%)")
        def highlight_row(row):
            color = "#d4edda" if row.Edge > 0 else "#f8d7da"
            return [f"background-color: {color}" for _ in row]

        st.dataframe(top_value_bets.style.apply(highlight_row, axis=1))
        st.caption("Πράσινο = πιθανό value bet, Κόκκινο = όχι value.")
    else:
        st.info("Δεν βρέθηκαν αποδόσεις για τους σημερινούς αγώνες.")
