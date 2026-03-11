import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weather Intelligence",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background-color: #FAFBFF !important;
  }
  [data-testid="stHeader"] { background-color: #FAFBFF !important; }
  [data-testid="stSidebar"] { background-color: #F0F4FF !important; }

  .card {
      background: #FFFFFF;
      border-radius: 16px;
      padding: 20px 24px;
      box-shadow: 0 2px 12px rgba(74,144,217,0.10);
      margin-bottom: 16px;
  }
  .hero-title {
      font-size: 2.8rem;
      font-weight: 800;
      color: #1A1A2E;
      line-height: 1.1;
  }
  .hero-sub { font-size: 1.1rem; color: #5A6A8A; margin-top: 4px; }
  .temp-hero { font-size: 5rem; font-weight: 900; color: #FF6B35; line-height: 1; }
  .feels-like { font-size: 1.1rem; color: #5A6A8A; }
  .weather-desc { font-size: 1.4rem; font-weight: 600; color: #1A1A2E; margin-top: 4px; }
  .score-label { font-size: 1rem; font-weight: 600; color: #1A1A2E; }
  .score-bar-bg { background: #E8EEF8; border-radius: 999px; height: 18px; overflow: hidden; margin: 8px 0; }
  .score-bar-fill { height: 18px; border-radius: 999px; }
  .badge-yes {
      display: inline-block; background: #E8FBF5; color: #05A87A;
      border: 1.5px solid #06D6A0; border-radius: 999px;
      padding: 4px 14px; font-size: 0.85rem; font-weight: 600; margin: 3px;
  }
  .badge-no {
      display: inline-block; background: #FFF0F3; color: #C0305A;
      border: 1.5px solid #EF476F; border-radius: 999px;
      padding: 4px 14px; font-size: 0.85rem; font-weight: 600; margin: 3px;
  }
  .badge-warn {
      display: inline-block; background: #FFFBEC; color: #B07800;
      border: 1.5px solid #FFD166; border-radius: 999px;
      padding: 4px 14px; font-size: 0.85rem; font-weight: 600; margin: 3px;
  }
  .day-card {
      background: #FFFFFF; border-radius: 14px; padding: 12px 8px;
      box-shadow: 0 2px 8px rgba(74,144,217,0.09); text-align: center; margin: 4px;
  }
  .day-name { font-size: 0.8rem; font-weight: 700; color: #5A6A8A; text-transform: uppercase; letter-spacing: 0.06em; }
  .day-emoji { font-size: 1.8rem; }
  .day-max { font-size: 1.1rem; font-weight: 800; color: #EF476F; }
  .day-min { font-size: 0.9rem; color: #4A90D9; font-weight: 600; }
  .day-rain { font-size: 0.78rem; color: #5A6A8A; margin-top: 2px; }
  .aqi-badge { display: inline-block; border-radius: 14px; padding: 18px 36px; font-size: 2.8rem; font-weight: 900; margin-bottom: 8px; }
  .divider { border: none; border-top: 1.5px solid #E8EEF8; margin: 18px 0; }
  .footer { text-align: center; color: #A0AABF; font-size: 0.78rem; margin-top: 32px; }
</style>
""", unsafe_allow_html=True)

# ─── WMO WEATHER CODE MAPPING ────────────────────────────────────────────────
WMO_CODES = {
    0:  ("Clear Sky",            "☀️"),
    1:  ("Mainly Clear",         "🌤️"),
    2:  ("Partly Cloudy",        "⛅"),
    3:  ("Overcast",             "☁️"),
    45: ("Foggy",                "🌫️"),
    48: ("Icy Fog",              "🌫️"),
    51: ("Light Drizzle",        "🌦️"),
    53: ("Moderate Drizzle",     "🌦️"),
    55: ("Dense Drizzle",        "🌧️"),
    61: ("Slight Rain",          "🌧️"),
    63: ("Moderate Rain",        "🌧️"),
    65: ("Heavy Rain",           "🌧️"),
    71: ("Slight Snow",          "🌨️"),
    73: ("Moderate Snow",        "🌨️"),
    75: ("Heavy Snow",           "❄️"),
    77: ("Snow Grains",          "❄️"),
    80: ("Slight Showers",       "🌦️"),
    81: ("Moderate Showers",     "🌧️"),
    82: ("Violent Showers",      "⛈️"),
    85: ("Snow Showers",         "🌨️"),
    86: ("Heavy Snow Showers",   "❄️"),
    95: ("Thunderstorm",         "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"),
    99: ("Thunderstorm w/ Hail", "⛈️"),
}

def wmo_label(code):
    return WMO_CODES.get(int(code) if code is not None else 0, ("Unknown", "🌡️"))

# ─── API HELPERS ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def geocode(city: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "WeatherIntelligenceApp/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if not data:
            return None
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "wind_speed_10m", "wind_direction_10m",
            "weather_code", "cloud_cover", "surface_pressure", "uv_index",
        ]),
        "hourly": ",".join([
            "temperature_2m", "precipitation_probability",
            "wind_speed_10m", "relative_humidity_2m",
        ]),
        "daily": ",".join([
            "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "uv_index_max", "wind_speed_10m_max", "sunrise", "sunset", "weather_code",
        ]),
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_air_quality(lat: float, lon: float):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "pm2_5,pm10,european_aqi,uv_index",
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception:
        return None

# ─── SCORE ALGORITHM ─────────────────────────────────────────────────────────
def weather_score(temp, precip_prob, wind, uv):
    score = 100.0
    score -= max(0, abs(temp - 21) * 3)
    score -= precip_prob * 0.5
    score -= max(0, (wind - 20) * 1.5)
    score -= max(0, (uv - 6) * 5)
    return int(max(0, min(100, score)))

def score_label(s):
    if s >= 80: return "Perfect day! 🌟", "#06D6A0"
    if s >= 60: return "Good day 😊",     "#4A90D9"
    if s >= 40: return "Fair day 😐",     "#FFD166"
    if s >= 20: return "Poor day 😕",     "#FF6B35"
    return "Stay indoors 🏠",             "#EF476F"

# ─── PLOTLY BASE LAYOUT ──────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="sans-serif", color="#1A1A2E"),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=False),
)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 12px 0 6px 0;">
  <span class="hero-title">🌤️ Weather Intelligence</span><br>
  <span class="hero-sub">Actionable weather insights · Powered by Open-Meteo &amp; OpenStreetMap · No API key needed</span>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ─── SEARCH BAR ──────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    city = st.text_input("🔍 City", value="Paris", label_visibility="collapsed",
                         placeholder="Enter any city in the world…")
with col_btn:
    search_clicked = st.button("Get Weather ➜", use_container_width=True, type="primary")

# ─── MAIN LOGIC ──────────────────────────────────────────────────────────────
if search_clicked or city:
    with st.spinner(f"Fetching intelligence for **{city}**…"):
        geo = geocode(city)

    if geo is None:
        st.error(f"❌ Could not find **{city}**. Try a different spelling or a nearby major city.")
        st.stop()

    lat, lon = geo["lat"], geo["lon"]
    display_name = geo["display_name"].split(",")[0]

    weather = fetch_weather(lat, lon)
    aq      = fetch_air_quality(lat, lon)

    if weather is None:
        st.warning("⚠️ Could not reach the weather API. Please try again in a moment.")
        st.stop()

    cur   = weather.get("current", {})
    hrly  = weather.get("hourly", {})
    daily = weather.get("daily", {})

    temp     = cur.get("temperature_2m", 0)
    feels    = cur.get("apparent_temperature", 0)
    humidity = cur.get("relative_humidity_2m", 0)
    wind     = cur.get("wind_speed_10m", 0)
    precip   = cur.get("precipitation", 0)
    cloud    = cur.get("cloud_cover", 0)
    pressure = cur.get("surface_pressure", 0)
    uv       = cur.get("uv_index", 0)
    wcode    = cur.get("weather_code", 0)
    desc, emoji = wmo_label(wcode)

    hr_times  = pd.to_datetime(hrly.get("time", []))
    hr_temp   = hrly.get("temperature_2m", [])
    hr_precip = hrly.get("precipitation_probability", [])
    hr_wind   = hrly.get("wind_speed_10m", [])
    hr_hum    = hrly.get("relative_humidity_2m", [])

    df_hourly = pd.DataFrame({
        "time":        hr_times,
        "temp":        hr_temp,
        "precip_prob": hr_precip,
        "wind":        hr_wind,
        "humidity":    hr_hum,
    })
    now   = pd.Timestamp.now(tz=None)
    df_24 = df_hourly[df_hourly["time"] >= now].head(24).copy()

    d_dates   = pd.to_datetime(daily.get("time", []))
    d_max     = daily.get("temperature_2m_max", [])
    d_min     = daily.get("temperature_2m_min", [])
    d_rain    = daily.get("precipitation_sum", [])
    d_uv      = daily.get("uv_index_max", [])
    d_wind    = daily.get("wind_speed_10m_max", [])
    d_sunrise = daily.get("sunrise", [])
    d_sunset  = daily.get("sunset", [])
    d_wcodes  = daily.get("weather_code", [])

    df_daily = pd.DataFrame({
        "date": d_dates, "max": d_max, "min": d_min,
        "rain": d_rain,  "uv": d_uv,  "wind": d_wind,
        "sunrise": d_sunrise, "sunset": d_sunset, "wcode": d_wcodes,
    })
    df_daily["day_name"] = df_daily["date"].dt.strftime("%a")

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌡️ Now", "📅 7-Day Forecast", "🕐 Hourly", "💨 Air Quality", "🗺️ Map"
    ])

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1 — NOW
    # ═══════════════════════════════════════════════════════════════════════
    with tab1:
        c1, c2 = st.columns([2, 3])

        with c1:
            st.markdown(f"""
            <div class="card" style="padding:28px 28px 20px 28px;">
              <div style="font-size:1rem;font-weight:700;color:#5A6A8A;letter-spacing:.05em;">
                📍 {display_name}
              </div>
              <div class="temp-hero">{temp:.0f}°C</div>
              <div class="feels-like">Feels like {feels:.0f}°C</div>
              <div class="weather-desc">{emoji} {desc}</div>
            </div>
            """, unsafe_allow_html=True)

            score      = weather_score(temp, hr_precip[0] if hr_precip else 0, wind, uv)
            slabel, sc = score_label(score)
            st.markdown(f"""
            <div class="card">
              <div class="score-label">🎯 Today's Weather Score</div>
              <div class="score-bar-bg">
                <div class="score-bar-fill" style="width:{score}%;background:{sc};"></div>
              </div>
              <div style="font-size:1.5rem;font-weight:800;color:{sc};">{score}/100 &nbsp;{slabel}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💧 Humidity",    f"{humidity}%")
            m2.metric("💨 Wind",        f"{wind:.0f} km/h")
            m3.metric("☀️ UV Index",    f"{uv:.1f}")
            m4.metric("☁️ Cloud Cover", f"{cloud}%")

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("🌧️ Precip Now",  f"{precip} mm")
            m6.metric("🔵 Pressure",    f"{pressure:.0f} hPa")
            if len(d_sunrise): m7.metric("🌅 Sunrise", d_sunrise[0][-5:])
            if len(d_sunset):  m8.metric("🌇 Sunset",  d_sunset[0][-5:])

            precip_p0 = hr_precip[0] if hr_precip else 0
            acts = [
                ("🚴 Cycling",   10 <= temp <= 28 and wind < 30 and precip_p0 < 30),
                ("🏃 Running",    5 <= temp <= 25 and precip_p0 < 40),
                ("🌿 Gardening", temp > 10 and precip_p0 < 20),
                ("☂️ Umbrella",  precip_p0 > 40),
                ("☀️ Sunscreen", uv > 3),
            ]
            badge_html = '<div class="card"><div style="font-weight:700;font-size:1rem;margin-bottom:8px;">🏅 Activity Recommendations</div>'
            for name, ok in acts:
                if name in ("☂️ Umbrella", "☀️ Sunscreen"):
                    cls = "badge-warn" if ok else "badge-yes"
                    txt = f"Bring {name}" if (ok and "Umbrella" in name) else \
                          f"Apply {name}" if ok else f"{name} Not needed"
                else:
                    cls = "badge-yes" if ok else "badge-no"
                    txt = f"{name} ✓" if ok else f"{name} ✗"
                badge_html += f'<span class="{cls}">{txt}</span>'
            badge_html += "</div>"
            st.markdown(badge_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2 — 7-DAY FORECAST
    # ═══════════════════════════════════════════════════════════════════════
    with tab2:
        if not df_daily.empty:
            fig7 = go.Figure()
            fig7.add_trace(go.Bar(
                x=df_daily["day_name"], y=df_daily["rain"],
                name="Rain (mm)", marker_color="rgba(74,144,217,0.35)", yaxis="y2",
            ))
            fig7.add_trace(go.Scatter(
                x=df_daily["day_name"], y=df_daily["max"],
                mode="lines+markers", name="Max °C",
                line=dict(color="#EF476F", width=3),
                marker=dict(size=8, color="#EF476F"),
            ))
            fig7.add_trace(go.Scatter(
                x=df_daily["day_name"], y=df_daily["min"],
                mode="lines+markers", name="Min °C",
                line=dict(color="#4A90D9", width=3),
                marker=dict(size=8, color="#4A90D9"),
            ))
            fig7.update_layout(
                **PLOT_LAYOUT,
                title="7-Day Temperature & Precipitation",
                title_font=dict(size=16, color="#1A1A2E"),
                legend=dict(orientation="h", y=1.12),
                yaxis=dict(title="Temperature (°C)", showgrid=True, gridcolor="#F0F4FF"),
                yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right",
                            showgrid=False, rangemode="tozero"),
                height=380,
            )
            st.plotly_chart(fig7, use_container_width=True)

            cols = st.columns(7)
            for i, row in df_daily.iterrows():
                _, em = wmo_label(row["wcode"])
                rain_val = row["rain"] if row["rain"] is not None else 0
                with cols[i % 7]:
                    st.markdown(f"""
                    <div class="day-card">
                      <div class="day-name">{row['day_name']}</div>
                      <div class="day-emoji">{em}</div>
                      <div class="day-max">{row['max']:.0f}°</div>
                      <div class="day-min">{row['min']:.0f}°</div>
                      <div class="day-rain">🌧️ {rain_val:.1f}mm</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3 — HOURLY
    # ═══════════════════════════════════════════════════════════════════════
    with tab3:
        if not df_24.empty:
            fig_temp = go.Figure()
            fig_temp.add_hrect(y0=18, y1=24,
                               fillcolor="rgba(6,214,160,0.08)", line_width=0,
                               annotation_text="Comfort zone",
                               annotation_position="top left",
                               annotation_font=dict(color="#06D6A0", size=11))
            fig_temp.add_trace(go.Scatter(
                x=df_24["time"], y=df_24["temp"],
                mode="lines", name="Temperature",
                line=dict(color="#FF6B35", width=3, shape="spline"),
                fill="tozeroy", fillcolor="rgba(255,107,53,0.10)",
            ))
            fig_temp.update_layout(
                **PLOT_LAYOUT,
                title="Hourly Temperature — Next 24h",
                title_font=dict(size=15, color="#1A1A2E"),
                yaxis_title="°C", height=300,
            )
            st.plotly_chart(fig_temp, use_container_width=True)

            fig_pp = go.Figure()
            fig_pp.add_trace(go.Bar(
                x=df_24["time"], y=df_24["precip_prob"],
                name="Precip Probability",
                marker_color=[
                    "#4A90D9" if v < 40 else "#FFD166" if v < 70 else "#EF476F"
                    for v in df_24["precip_prob"].fillna(0)
                ],
            ))
            fig_pp.update_layout(
                **PLOT_LAYOUT,
                title="Precipitation Probability — Next 24h",
                title_font=dict(size=15, color="#1A1A2E"),
                yaxis=dict(title="%", range=[0, 100], showgrid=True, gridcolor="#F0F4FF"),
                height=260,
            )
            st.plotly_chart(fig_pp, use_container_width=True)

            df_12 = df_24.head(12).copy()
            df_12["go_score"] = (
                100
                - df_12["precip_prob"].fillna(0) * 0.8
                - (df_12["temp"] - 21).abs() * 2
                - df_12["wind"].fillna(0) * 0.5
            )
            best_row  = df_12.loc[df_12["go_score"].idxmax()]
            best_time = best_row["time"].strftime("%H:%M")
            st.markdown(f"""
            <div class="card" style="text-align:center;">
              <div style="font-size:1rem;color:#5A6A8A;font-weight:600;">⏰ Best Time to Go Outside (Next 12h)</div>
              <div style="font-size:2.4rem;font-weight:900;color:#FF6B35;">{best_time}</div>
              <div style="font-size:1rem;color:#1A1A2E;">
                Expected {best_row['temp']:.1f}°C · {best_row['precip_prob']:.0f}% rain · {best_row['wind']:.0f} km/h wind
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 4 — AIR QUALITY
    # ═══════════════════════════════════════════════════════════════════════
    with tab4:
        if aq:
            aq_hrly  = aq.get("hourly", {})
            aq_times = pd.to_datetime(aq_hrly.get("time", []))
            aq_aqi   = aq_hrly.get("european_aqi", [])
            aq_pm25  = aq_hrly.get("pm2_5", [])
            aq_pm10  = aq_hrly.get("pm10", [])

            df_aq     = pd.DataFrame({"time": aq_times, "aqi": aq_aqi,
                                      "pm25": aq_pm25, "pm10": aq_pm10})
            df_aq_now = df_aq[df_aq["time"] >= now].head(48)

            cur_aqi  = next((v for v in aq_aqi  if v is not None), 0)
            cur_pm25 = next((v for v in aq_pm25 if v is not None), 0)
            cur_pm10 = next((v for v in aq_pm10 if v is not None), 0)

            def aqi_color(v):
                if v <= 20: return "#06D6A0"
                if v <= 40: return "#FFD166"
                if v <= 60: return "#FF6B35"
                if v <= 80: return "#EF476F"
                return "#9B2DD4"

            def aqi_label(v):
                if v <= 20: return "🟢 Excellent"
                if v <= 40: return "🟡 Good"
                if v <= 60: return "🟠 Moderate"
                if v <= 80: return "🔴 Poor"
                return "🟣 Very Poor"

            def aqi_advice(v):
                if v <= 20: return "Air quality is excellent. Enjoy outdoor activities freely!"
                if v <= 40: return "Air quality is good. Suitable for all outdoor activities."
                if v <= 60: return "Moderate air quality. Sensitive groups should limit prolonged outdoor exertion."
                if v <= 80: return "Poor air quality. Everyone should reduce outdoor activities."
                return "Very poor air quality. Avoid outdoors. Consider wearing a mask."

            a1, a2 = st.columns([1, 2])
            with a1:
                aqi_c = aqi_color(cur_aqi)
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                  <div style="font-size:.9rem;font-weight:700;color:#5A6A8A;letter-spacing:.05em;">EUROPEAN AQI</div>
                  <div class="aqi-badge" style="background:{aqi_c}22;color:{aqi_c};">{cur_aqi:.0f}</div>
                  <div style="font-size:1.3rem;font-weight:800;color:{aqi_c};">{aqi_label(cur_aqi)}</div>
                  <hr class="divider">
                  <div style="font-size:.92rem;color:#1A1A2E;">{aqi_advice(cur_aqi)}</div>
                </div>
                """, unsafe_allow_html=True)
                st.metric("🔬 PM2.5", f"{cur_pm25:.1f} µg/m³" if cur_pm25 else "N/A")
                st.metric("🔬 PM10",  f"{cur_pm10:.1f} µg/m³" if cur_pm10 else "N/A")

            with a2:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=cur_aqi,
                    title={"text": "Air Quality Index", "font": {"size": 16, "color": "#1A1A2E"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#1A1A2E"},
                        "bar":  {"color": aqi_c, "thickness": 0.25},
                        "bgcolor": "white",
                        "steps": [
                            {"range": [0,  20], "color": "rgba(6,214,160,0.15)"},
                            {"range": [20, 40], "color": "rgba(255,209,102,0.15)"},
                            {"range": [40, 60], "color": "rgba(255,107,53,0.15)"},
                            {"range": [60, 80], "color": "rgba(239,71,111,0.15)"},
                            {"range": [80,100], "color": "rgba(155,45,212,0.15)"},
                        ],
                        "threshold": {"line": {"color": aqi_c, "width": 4}, "value": cur_aqi},
                    }
                ))
                fig_gauge.update_layout(
                    paper_bgcolor="white", plot_bgcolor="white",
                    height=300, margin=dict(l=20, r=20, t=40, b=10),
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            if not df_aq_now.empty:
                fig_aqi = go.Figure()
                fig_aqi.add_trace(go.Bar(
                    x=df_aq_now["time"], y=df_aq_now["aqi"],
                    marker_color=[aqi_color(v) if v is not None else "#ccc"
                                  for v in df_aq_now["aqi"]],
                    name="AQI",
                ))
                fig_aqi.update_layout(
                    **PLOT_LAYOUT,
                    title="European AQI — Next 48h",
                    title_font=dict(size=15, color="#1A1A2E"),
                    yaxis_title="AQI", height=260,
                )
                st.plotly_chart(fig_aqi, use_container_width=True)
        else:
            st.warning("Air quality data unavailable for this location.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 5 — MAP
    # ═══════════════════════════════════════════════════════════════════════
    with tab5:
        map_df = pd.DataFrame({
            "lat":   [lat],
            "lon":   [lon],
            "city":  [display_name],
            "label": [f"{display_name} · {temp:.0f}°C {emoji}"],
            "temp":  [temp],
        })
        fig_map = px.scatter_mapbox(
            map_df, lat="lat", lon="lon",
            hover_name="label",
            hover_data={"lat": False, "lon": False, "city": False,
                        "temp": True, "label": False},
            zoom=9, height=520,
            mapbox_style="open-street-map",
            color_discrete_sequence=["#FF6B35"],
            size=[20], size_max=20,
        )
        fig_map.update_layout(paper_bgcolor="white", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_map, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("📍 Latitude",  f"{lat:.4f}°")
        c2.metric("📍 Longitude", f"{lon:.4f}°")
        c3.metric("🌡️ Now",       f"{temp:.0f}°C {emoji}")

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  Data: <a href="https://open-meteo.com" target="_blank">Open-Meteo.com</a> (CC BY 4.0) ·
  Geocoding: <a href="https://nominatim.org" target="_blank">Nominatim / OpenStreetMap</a> ·
  Built with <a href="https://streamlit.io" target="_blank">Streamlit</a> 🌤️
</div>
""", unsafe_allow_html=True)
