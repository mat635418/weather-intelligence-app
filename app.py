import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import math
import streamlit.components.v1 as components

# === PAGE CONFIG ============================================================
st.set_page_config(
    page_title="Weather Intelligence",
    page_icon="\U0001f324\ufe0f",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# === GLOBAL CSS =============================================================
st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background-color: #FAFBFF !important;
  }
  [data-testid="stHeader"] { background-color: #FAFBFF !important; }
  [data-testid="stSidebar"] { background-color: #F0F4FF !important; }

  .card {
      background: rgba(255,255,255,0.65);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1.5px solid rgba(255,255,255,0.85);
      border-radius: 20px;
      padding: 20px 24px;
      box-shadow: 0 4px 24px rgba(74,144,217,0.13);
      margin-bottom: 16px;
  }
  .hero-title { font-size: 2.8rem; font-weight: 800; color: #1A1A2E; line-height: 1.1; }
  .hero-sub { font-size: 1.1rem; color: #5A6A8A; margin-top: 4px; }
  .temp-hero {
      font-size: 5rem; font-weight: 900; line-height: 1;
      background: linear-gradient(135deg, #FF6B35 0%, #A855F7 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
  }
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
      background: rgba(255,255,255,0.65);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1.5px solid rgba(255,255,255,0.85);
      border-radius: 16px; padding: 12px 8px;
      box-shadow: 0 4px 16px rgba(74,144,217,0.10);
      text-align: center; margin: 4px;
  }
  .day-name { font-size: 0.8rem; font-weight: 700; color: #5A6A8A; text-transform: uppercase; letter-spacing: 0.06em; }
  .day-emoji { font-size: 1.8rem; }
  .day-max { font-size: 1.1rem; font-weight: 800; color: #EF476F; }
  .day-min { font-size: 0.9rem; color: #4A90D9; font-weight: 600; }
  .day-rain { font-size: 0.78rem; color: #5A6A8A; margin-top: 2px; }
  .aqi-badge { display: inline-block; border-radius: 14px; padding: 18px 36px; font-size: 2.8rem; font-weight: 900; margin-bottom: 8px; }
  .divider { border: none; border-top: 1.5px solid #E8EEF8; margin: 18px 0; }
  .footer { text-align: center; color: #A0AABF; font-size: 0.78rem; margin-top: 32px; }

  [data-testid="stTabs"] [data-baseweb="tab"] {
      border-radius: 999px !important; padding: 6px 20px !important;
      font-weight: 700 !important; font-size: 0.9rem !important;
      background: transparent !important; border: 2px solid transparent !important;
      transition: all 0.2s ease !important;
  }
  [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
      background: linear-gradient(135deg, #FF6B35, #A855F7) !important;
      color: white !important; border: none !important;
  }
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
  [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

  @keyframes float-up {
      0%   { transform: translateY(0);      opacity: 0.18; }
      100% { transform: translateY(-120px); opacity: 0;    }
  }
</style>
""", unsafe_allow_html=True)

# === WMO WEATHER CODE MAPPING ===============================================
WMO_CODES = {
    0:  ("Clear Sky",            "\u2600\ufe0f"),
    1:  ("Mainly Clear",         "\U0001f324\ufe0f"),
    2:  ("Partly Cloudy",        "\u26c5"),
    3:  ("Overcast",             "\u2601\ufe0f"),
    45: ("Foggy",                "\U0001f32b\ufe0f"),
    48: ("Icy Fog",              "\U0001f32b\ufe0f"),
    51: ("Light Drizzle",        "\U0001f326\ufe0f"),
    53: ("Moderate Drizzle",     "\U0001f326\ufe0f"),
    55: ("Dense Drizzle",        "\U0001f327\ufe0f"),
    61: ("Slight Rain",          "\U0001f327\ufe0f"),
    63: ("Moderate Rain",        "\U0001f327\ufe0f"),
    65: ("Heavy Rain",           "\U0001f327\ufe0f"),
    71: ("Slight Snow",          "\U0001f328\ufe0f"),
    73: ("Moderate Snow",        "\U0001f328\ufe0f"),
    75: ("Heavy Snow",           "\u2744\ufe0f"),
    77: ("Snow Grains",          "\u2744\ufe0f"),
    80: ("Slight Showers",       "\U0001f326\ufe0f"),
    81: ("Moderate Showers",     "\U0001f327\ufe0f"),
    82: ("Violent Showers",      "\u26c8\ufe0f"),
    85: ("Snow Showers",         "\U0001f328\ufe0f"),
    86: ("Heavy Snow Showers",   "\u2744\ufe0f"),
    95: ("Thunderstorm",         "\u26c8\ufe0f"),
    96: ("Thunderstorm w/ Hail", "\u26c8\ufe0f"),
    99: ("Thunderstorm w/ Hail", "\u26c8\ufe0f"),
}

def wmo_label(code):
    return WMO_CODES.get(int(code) if code is not None else 0, ("Unknown", "\U0001f321\ufe0f"))

# === MAJOR CITIES LIST ======================================================
MAJOR_CITIES = [
    ("London",       51.5074,  -0.1278),  ("Paris",        48.8566,   2.3522),
    ("Berlin",       52.5200,  13.4050),  ("Madrid",       40.4168,  -3.7038),
    ("Rome",         41.9028,  12.4964),  ("Amsterdam",    52.3676,   4.9041),
    ("Vienna",       48.2082,  16.3738),  ("Brussels",     50.8503,   4.3517),
    ("New York",     40.7128, -74.0060),  ("Los Angeles",  34.0522, -118.2437),
    ("Chicago",      41.8781, -87.6298),  ("Toronto",      43.6532,  -79.3832),
    ("Tokyo",        35.6762, 139.6503),  ("Beijing",      39.9042,  116.4074),
    ("Shanghai",     31.2304, 121.4737),  ("Sydney",      -33.8688,  151.2093),
    ("Dubai",        25.2048,  55.2708),  ("Singapore",     1.3521,  103.8198),
    ("Mumbai",       19.0760,  72.8777),  ("Sao Paulo",   -23.5505,  -46.6333),
    ("Buenos Aires",-34.6037, -58.3816),  ("Cairo",        30.0444,   31.2357),
    ("Lagos",         6.5244,   3.3792),  ("Johannesburg",-26.2041,   28.0473),
    ("Mexico City",  19.4326,  -99.1332), ("Moscow",       55.7558,   37.6173),
    ("Istanbul",     41.0082,  28.9784),  ("Seoul",        37.5665,  126.9780),
    ("Bangkok",      13.7563, 100.5018),  ("Jakarta",      -6.2088,  106.8456),
]

# === API HELPERS =============================================================
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
def reverse_geocode(lat: float, lon: float):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json"}
    headers = {"User-Agent": "WeatherIntelligenceApp/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        address = data.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or data.get("display_name", "").split(",")[0]
        )
        return city
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
            "wind_speed_10m", "relative_humidity_2m", "apparent_temperature",
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
def fetch_current_only(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
        "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        cur = data.get("current", {})
        return {
            "temp":       cur.get("temperature_2m",     0) or 0,
            "wind_speed": cur.get("wind_speed_10m",     0) or 0,
            "wind_dir":   cur.get("wind_direction_10m", 0) or 0,
        }
    except Exception:
        return {"temp": 0, "wind_speed": 0, "wind_dir": 0}

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

# === SCORE ALGORITHM =========================================================
def weather_score(temp, precip_prob, wind, uv):
    score = 100.0
    score -= max(0, abs(temp - 21) * 3)
    score -= precip_prob * 0.5
    score -= max(0, (wind - 20) * 1.5)
    score -= max(0, (uv - 6) * 5)
    return int(max(0, min(100, score)))

def score_label(s):
    if s >= 80: return "Perfect day! \U0001f31f", "#06D6A0"
    if s >= 60: return "Good day \U0001f60a",     "#4A90D9"
    if s >= 40: return "Fair day \U0001f610",     "#FFD166"
    if s >= 20: return "Poor day \U0001f615",     "#FF6B35"
    return "Stay indoors \U0001f3e0",             "#EF476F"

# === HELPER: DYNAMIC BACKGROUND GRADIENT ====================================
def get_bg_gradient(wcode):
    if wcode in (0, 1):
        return "linear-gradient(135deg, #FFF8F0 0%, #FFE8D6 100%)"
    elif wcode in (2, 3):
        return "linear-gradient(135deg, #F0F4FF 0%, #E8EEF8 100%)"
    elif wcode in (71, 73, 75, 77, 85, 86):
        return "linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%)"
    elif 51 <= wcode <= 82:
        return "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)"
    elif wcode in (95, 96, 99):
        return "linear-gradient(135deg, #FDF4FF 0%, #EDE9FE 100%)"
    return "linear-gradient(135deg, #FAFBFF 0%, #F0F4FF 100%)"

# === HELPER: WEATHER PERSONALITY ============================================
def weather_personality(score, wcode):
    if score >= 85 and wcode in (0, 1):
        return ("\U0001f3d6\ufe0f Beach Day Vibes", "Nothing but blue skies and good vibes!")
    if score >= 70 and wcode in (0, 1, 2):
        return ("\U0001f33f Perfect Picnic Weather", "Grab a blanket and head outside!")
    if score >= 60:
        return ("\U0001f60a Get Outside & Chill", "Pretty solid weather \u2014 make the most of it!")
    if wcode in (95, 96, 99):
        return ("\u26a1 Storm Chaser Alert", "Thunder rumbling \u2014 stay safe or embrace the drama!")
    if wcode in (71, 73, 75, 77, 85, 86):
        return ("\u26f7\ufe0f Snow Day! \u2744\ufe0f", "Dust off the skis or build a snowman!")
    if wcode in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return ("\U0001f3a7 Cozy Indoors Weather", "Hot drinks, good books, lo-fi beats.")
    if score < 30:
        return ("\U0001f3e0 Stay In, Order Pizza", "Not the day for outdoor adventures. Netflix it is.")
    return ("\U0001f4da A Regular Kind of Day", "Nothing special, nothing terrible. Just a day.")

# === HELPER: CIRCLE POINTS ==================================================
def circle_points(center_lat, center_lon, radius_km, n=60):
    R = 6371  # Earth's mean radius in km
    lats, lons = [], []
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        dlat = (radius_km / R) * math.cos(angle) * (180 / math.pi)
        dlon = (radius_km / R) * math.sin(angle) * (180 / math.pi) / math.cos(math.radians(center_lat))
        lats.append(center_lat + dlat)
        lons.append(center_lon + dlon)
    return lats, lons

# === HELPER: WIND DIRECTION ARROW ===========================================
def wind_arrow(wind_dir):
    dirs = ["\u2193", "\u2199", "\u2190", "\u2196", "\u2191", "\u2197", "\u2192", "\u2198"]
    idx = int((wind_dir + 22.5) / 45) % 8
    return dirs[idx]

# === HELPER: SPARKLINE SVG ==================================================
def make_sparkline_svg(values, max_height=18, bar_width=4, gap=1):
    if not values:
        return ""
    clean = [float(v) if v is not None else 0.0 for v in values]
    max_val = max(clean) if max(clean) > 0 else 1.0
    bars = []
    total_width = len(clean) * (bar_width + gap) - gap
    for i, v in enumerate(clean):
        bar_h = max(1, int((v / max_val) * max_height))
        x = i * (bar_width + gap)
        y = max_height - bar_h
        color = "#4A90D9" if v < 40 else "#FFD166" if v < 70 else "#EF476F"
        bars.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" fill="{color}" rx="1"/>'
        )
    return (
        f'<svg width="{total_width}" height="{max_height}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(bars)}</svg>'
    )

# === HELPER: FIND NEARBY CITIES =============================================
def find_nearby_cities(lat, lon, n=4):
    dists = []
    for name, clat, clon in MAJOR_CITIES:
        # Exclude cities within ~55 km (0.5 degrees) of the searched location
        if abs(clat - lat) < 0.5 and abs(clon - lon) < 0.5:
            continue
        dist = ((clat - lat) ** 2 + (clon - lon) ** 2) ** 0.5
        dists.append((dist, name, clat, clon))
    dists.sort(key=lambda x: x[0])
    return [(name, clat, clon) for _, name, clat, clon in dists[:n]]

# === PLOTLY BASE LAYOUT =====================================================
PLOT_LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="sans-serif", color="#1A1A2E"),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=False),
    yaxis=dict(showgrid=True, gridcolor="#F0F4FF", zeroline=False),
)
PLOT_LAYOUT_NO_YAXIS = {k: v for k, v in PLOT_LAYOUT.items() if k != "yaxis"}

# === HEADER =================================================================
st.markdown("""
<div style="padding: 12px 0 6px 0;">
  <span class="hero-title">\U0001f324\ufe0f Weather Intelligence</span><br>
  <span class="hero-sub">Actionable weather insights &middot; Powered by Open-Meteo &amp; OpenStreetMap &middot; No API key needed</span>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# === AUTO-DETECT LOCATION (query params) ====================================
qp = st.query_params
default_city = "Paris"
if "lat" in qp and "lon" in qp:
    try:
        gp_lat = float(qp["lat"])
        gp_lon = float(qp["lon"])
        detected = reverse_geocode(gp_lat, gp_lon)
        if detected:
            default_city = detected
    except Exception:
        pass

# === SEARCH BAR =============================================================
col_input, col_btn, col_geo = st.columns([4, 1, 1])
with col_input:
    city = st.text_input(
        "\U0001f50d City", value=default_city, label_visibility="collapsed",
        placeholder="Enter any city in the world\u2026",
    )
with col_btn:
    search_clicked = st.button("Get Weather \u27a4", use_container_width=True, type="primary")
with col_geo:
    components.html(
        """<button onclick="navigator.geolocation.getCurrentPosition("""
        """function(p){window.parent.location.search='?lat='+p.coords.latitude.toFixed(4)"""
        """+'&lon='+p.coords.longitude.toFixed(4)},"""
        """function(e){alert('Location access denied or unavailable. Please type your city manually.');});" """
        """style="width:100%;height:38px;border-radius:8px;"""
        """background:linear-gradient(135deg,#4A90D9,#06D6A0);"""
        """color:white;border:none;cursor:pointer;font-weight:700;font-size:0.8rem;">"""
        """\U0001f4cd My Location</button>""",
        height=46,
    )

# === COMPARE CITY EXPANDER ==================================================
with st.expander("\u2696\ufe0f Compare with another city"):
    city2_input = st.text_input(
        "City to compare", key="city2_text", placeholder="e.g. London, Berlin\u2026"
    )
    col_cmp1, col_cmp2 = st.columns(2)
    with col_cmp1:
        compare_btn = st.button("\u2696\ufe0f Compare", key="do_compare")
    with col_cmp2:
        clear_btn = st.button("\u2715 Clear", key="clear_compare")
    if compare_btn:
        st.session_state["city2"] = city2_input
        st.session_state["compare_active"] = True
    if clear_btn:
        st.session_state["city2"] = ""
        st.session_state["compare_active"] = False

city2 = st.session_state.get("city2", "")
compare_active = st.session_state.get("compare_active", False) and bool(city2)

# === MAIN LOGIC =============================================================
if search_clicked or city:
    with st.spinner(f"Fetching intelligence for **{city}**\u2026"):
        geo = geocode(city)

    if geo is None:
        st.error(f"\u274c Could not find **{city}**. Try a different spelling or a nearby major city.")
        st.stop()

    lat, lon = geo["lat"], geo["lon"]
    display_name = geo["display_name"].split(",")[0]

    weather = fetch_weather(lat, lon)
    aq      = fetch_air_quality(lat, lon)

    if weather is None:
        st.warning("\u26a0\ufe0f Could not reach the weather API. Please try again in a moment.")
        st.stop()

    cur   = weather.get("current", {})
    hrly  = weather.get("hourly", {})
    daily = weather.get("daily", {})

    temp     = cur.get("temperature_2m",     0) or 0
    feels    = cur.get("apparent_temperature",0) or 0
    humidity = cur.get("relative_humidity_2m",0) or 0
    wind     = cur.get("wind_speed_10m",      0) or 0
    precip   = cur.get("precipitation",       0) or 0
    cloud    = cur.get("cloud_cover",         0) or 0
    pressure = cur.get("surface_pressure",    0) or 0
    uv       = cur.get("uv_index",            0) or 0
    wcode    = cur.get("weather_code",        0) or 0
    desc, emoji = wmo_label(wcode)

    hr_times  = pd.to_datetime(hrly.get("time", []))
    hr_temp   = hrly.get("temperature_2m", [])
    hr_precip = hrly.get("precipitation_probability", [])
    hr_wind   = hrly.get("wind_speed_10m", [])
    hr_hum    = hrly.get("relative_humidity_2m", [])
    hr_feels  = hrly.get("apparent_temperature", [])

    feels_col = hr_feels if len(hr_feels) == len(hr_times) else [None] * len(hr_times)
    df_hourly = pd.DataFrame({
        "time":        hr_times,
        "temp":        hr_temp,
        "precip_prob": hr_precip,
        "wind":        hr_wind,
        "humidity":    hr_hum,
        "feels_like":  feels_col,
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

    # Enhancement 10: Dynamic pastel gradient background
    bg_grad = get_bg_gradient(wcode)
    st.markdown(
        f'<style>html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]'
        f'{{background:{bg_grad}!important}}'
        f'[data-testid="stHeader"]{{background:{bg_grad}!important}}</style>',
        unsafe_allow_html=True,
    )

    # Fetch city2 for comparison
    weather2 = None
    geo2     = None
    if compare_active:
        with st.spinner(f"Fetching data for **{city2}**\u2026"):
            geo2 = geocode(city2)
        if geo2:
            weather2 = fetch_weather(geo2["lat"], geo2["lon"])
        if not geo2 or not weather2:
            st.warning(f"\u26a0\ufe0f Could not fetch data for **{city2}**. Showing normal view.")
            compare_active = False

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "\U0001f321\ufe0f Now", "\U0001f4c5 7-Day Forecast",
        "\U0001f550 Hourly", "\U0001f4a8 Air Quality", "\U0001f5fa\ufe0f Map",
    ])

    # =========================================================================
    # TAB 1 - NOW
    # =========================================================================
    with tab1:
        precip_p0 = hr_precip[0] if hr_precip else 0
        score     = weather_score(temp, precip_p0, wind, uv)
        slabel, sc = score_label(score)

        # Enhancement 8: Floating emoji background
        if wcode in (0, 1):
            fe = ["\u2600\ufe0f","\U0001f31e","\u2728","\u2600\ufe0f","\U0001f324\ufe0f","\U0001f49b"]
        elif wcode in (2, 3):
            fe = ["\u26c5","\u2601\ufe0f","\U0001f324\ufe0f","\u26c5","\U0001f4a8","\u2601\ufe0f"]
        elif wcode in (71, 73, 75, 77, 85, 86):
            fe = ["\u2744\ufe0f","\u26c4","\U0001f328\ufe0f","\u2744\ufe0f","\U0001f9ca","\u26c4"]
        elif 51 <= wcode <= 82:
            fe = ["\U0001f327\ufe0f","\U0001f4a7","\u2614","\U0001f327\ufe0f","\U0001f4a6","\U0001f302"]
        elif wcode in (95, 96, 99):
            fe = ["\u26a1","\U0001f329\ufe0f","\u26c8\ufe0f","\u26a1","\U0001f32a\ufe0f","\U0001f49c"]
        else:
            fe = ["\U0001f324\ufe0f","\U0001f4a8","\U0001f32c\ufe0f","\U0001f321\ufe0f","\U0001f308","\u2601\ufe0f"]
        positions = [5, 15, 30, 50, 65, 80]
        durations = [6,  7,  8,  9,  8,  10]
        delays    = [0,  1,  2,  3,  4,   5]
        edivs = "".join([
            f'<div style="position:fixed;left:{positions[i]}%;bottom:10%;font-size:2rem;'
            f'pointer-events:none;z-index:0;opacity:0.18;'
            f'animation:float-up {durations[i]}s {delays[i]}s infinite;">'
            f'{fe[i]}</div>'
            for i in range(6)
        ])
        st.markdown(edivs, unsafe_allow_html=True)

        # Enhancement 18: Two-city comparison mode
        if compare_active and weather2:
            cur2   = weather2.get("current", {})
            hrly2  = weather2.get("hourly", {})
            temp2  = cur2.get("temperature_2m",     0) or 0
            feels2 = cur2.get("apparent_temperature",0) or 0
            hum2   = cur2.get("relative_humidity_2m",0) or 0
            wind2  = cur2.get("wind_speed_10m",      0) or 0
            uv2    = cur2.get("uv_index",            0) or 0
            wcode2 = cur2.get("weather_code",        0) or 0
            desc2, emoji2 = wmo_label(wcode2)
            prcp2  = hrly2.get("precipitation_probability", [])
            score2 = weather_score(temp2, prcp2[0] if prcp2 else 0, wind2, uv2)
            slabel2, sc2 = score_label(score2)
            dname2 = geo2["display_name"].split(",")[0]

            def _badge(val1, val2, mode="higher"):
                if mode == "higher":
                    w1 = val1 >= val2
                elif mode == "closer21":
                    w1 = abs(val1 - 21) <= abs(val2 - 21)
                elif mode == "closer50":
                    w1 = abs(val1 - 50) <= abs(val2 - 50)
                else:
                    w1 = val1 <= val2
                b = ('<span style="background:#E8FBF5;color:#05A87A;border:1.5px solid '
                     '#06D6A0;border-radius:999px;padding:2px 10px;font-size:0.75rem;'
                     'font-weight:700;"> \u2713 Better</span>')
                return (b, "") if w1 else ("", b)

            sb1, sb2 = _badge(score,    score2,   "higher")
            tb1, tb2 = _badge(temp,     temp2,    "closer21")
            hb1, hb2 = _badge(humidity, hum2,     "closer50")
            wb1, wb2 = _badge(wind,     wind2,    "lower")
            ub1, ub2 = _badge(uv,       uv2,      "lower")

            cmp1, cmp2 = st.columns(2)
            with cmp1:
                st.markdown(
                    f'<div class="card">'
                    f'<div style="font-size:1.2rem;font-weight:800;color:#1A1A2E;">\U0001f4cd {display_name}</div>'
                    f'<div class="temp-hero">{temp:.0f}\u00b0C</div>'
                    f'<div class="feels-like">Feels like {feels:.0f}\u00b0C {tb1}</div>'
                    f'<div class="weather-desc">{emoji} {desc}</div>'
                    f'<hr class="divider">'
                    f'<div>\U0001f3af Score: <b style="color:{sc};">{score}/100</b> {slabel} {sb1}</div>'
                    f'<div>\U0001f4a7 Humidity: {humidity}% {hb1}</div>'
                    f'<div>\U0001f4a8 Wind: {wind:.0f} km/h {wb1}</div>'
                    f'<div>\u2600\ufe0f UV: {uv:.1f} {ub1}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with cmp2:
                st.markdown(
                    f'<div class="card">'
                    f'<div style="font-size:1.2rem;font-weight:800;color:#1A1A2E;">\U0001f4cd {dname2}</div>'
                    f'<div class="temp-hero">{temp2:.0f}\u00b0C</div>'
                    f'<div class="feels-like">Feels like {feels2:.0f}\u00b0C {tb2}</div>'
                    f'<div class="weather-desc">{emoji2} {desc2}</div>'
                    f'<hr class="divider">'
                    f'<div>\U0001f3af Score: <b style="color:{sc2};">{score2}/100</b> {slabel2} {sb2}</div>'
                    f'<div>\U0001f4a7 Humidity: {hum2}% {hb2}</div>'
                    f'<div>\U0001f4a8 Wind: {wind2:.0f} km/h {wb2}</div>'
                    f'<div>\u2600\ufe0f UV: {uv2:.1f} {ub2}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        else:
            # Normal view
            c1, c2 = st.columns([2, 3])

            with c1:
                st.markdown(
                    f'<div class="card" style="padding:28px 28px 20px 28px;">'
                    f'<div style="font-size:1rem;font-weight:700;color:#5A6A8A;letter-spacing:.05em;">'
                    f'\U0001f4cd {display_name}</div>'
                    f'<div class="temp-hero">{temp:.0f}\u00b0C</div>'
                    f'<div class="feels-like">Feels like {feels:.0f}\u00b0C</div>'
                    f'<div class="weather-desc">{emoji} {desc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="card">'
                    f'<div class="score-label">\U0001f3af Today\'s Weather Score</div>'
                    f'<div class="score-bar-bg">'
                    f'<div class="score-bar-fill" style="width:{score}%;background:{sc};"></div>'
                    f'</div>'
                    f'<div style="font-size:1.5rem;font-weight:800;color:{sc};">{score}/100 &nbsp;{slabel}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Enhancement 13: Weather Personality card
                p_label, p_flavour = weather_personality(score, wcode)
                st.markdown(
                    f'<div class="card">'
                    f'<div style="font-size:1.6rem;font-weight:800;color:#1A1A2E;margin-bottom:4px;">{p_label}</div>'
                    f'<div style="font-size:0.9rem;color:#5A6A8A;">{p_flavour}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with c2:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("\U0001f4a7 Humidity",    f"{humidity}%")
                m2.metric("\U0001f4a8 Wind",        f"{wind:.0f} km/h")
                m3.metric("\u2600\ufe0f UV Index",  f"{uv:.1f}")
                m4.metric("\u2601\ufe0f Cloud Cover",f"{cloud}%")

                m5, m6, m7, m8 = st.columns(4)
                m5.metric("\U0001f327\ufe0f Precip Now", f"{precip} mm")
                m6.metric("\U0001f535 Pressure",   f"{pressure:.0f} hPa")
                if len(d_sunrise): m7.metric("\U0001f305 Sunrise", d_sunrise[0][-5:])
                if len(d_sunset):  m8.metric("\U0001f307 Sunset",  d_sunset[0][-5:])

                # Enhancement 15: Sunrise/sunset daylight progress bar
                if d_sunrise and d_sunset:
                    try:
                        sunrise_dt  = datetime.fromisoformat(d_sunrise[0])
                        sunset_dt   = datetime.fromisoformat(d_sunset[0])
                        now_dt      = datetime.now()
                        total_secs  = (sunset_dt - sunrise_dt).total_seconds()
                        elapsed     = (now_dt - sunrise_dt).total_seconds()
                        progress    = max(0.0, min(1.0, elapsed / total_secs)) if total_secs > 0 else 0.0
                        prog_pct    = int(progress * 100)
                        sunrise_str = sunrise_dt.strftime("%H:%M")
                        sunset_str  = sunset_dt.strftime("%H:%M")
                        st.markdown(
                            f'<div class="card" style="padding:14px 20px;">'
                            f'<div style="font-size:0.85rem;font-weight:700;color:#5A6A8A;margin-bottom:6px;">'
                            f'\U0001f305 Daylight Progress</div>'
                            f'<div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#5A6A8A;margin-bottom:4px;">'
                            f'<span>\U0001f305 {sunrise_str}</span><span>\U0001f307 {sunset_str}</span></div>'
                            f'<div style="background:#E8EEF8;border-radius:999px;height:14px;overflow:visible;position:relative;">'
                            f'<div style="width:{prog_pct}%;background:linear-gradient(90deg,#FFD166,#FF6B35);'
                            f'height:14px;border-radius:999px;position:relative;">'
                            f'<span style="position:absolute;right:-10px;top:-4px;font-size:1.3rem;">\u2600\ufe0f</span>'
                            f'</div></div></div>',
                            unsafe_allow_html=True,
                        )
                    except Exception:
                        pass

                acts = [
                    ("\U0001f6b4 Cycling",   10 <= temp <= 28 and wind < 30 and precip_p0 < 30),
                    ("\U0001f3c3 Running",    5 <= temp <= 25 and precip_p0 < 40),
                    ("\U0001f33f Gardening", temp > 10 and precip_p0 < 20),
                    ("\u2602\ufe0f Umbrella",  precip_p0 > 40),
                    ("\u2600\ufe0f Sunscreen", uv > 3),
                ]
                badge_html = (
                    '<div class="card">'
                    '<div style="font-weight:700;font-size:1rem;margin-bottom:8px;">'
                    '\U0001f3c5 Activity Recommendations</div>'
                )
                for name, ok in acts:
                    if name in ("\u2602\ufe0f Umbrella", "\u2600\ufe0f Sunscreen"):
                        cls = "badge-warn" if ok else "badge-yes"
                        txt = (f"Bring {name}" if (ok and "Umbrella" in name)
                               else f"Apply {name}" if ok else f"{name} Not needed")
                    else:
                        cls = "badge-yes" if ok else "badge-no"
                        txt = f"{name} \u2713" if ok else f"{name} \u2717"
                    badge_html += f'<span class="{cls}">{txt}</span>'
                badge_html += "</div>"
                st.markdown(badge_html, unsafe_allow_html=True)

                # Enhancement 16: Share weather summary
                with st.expander("\U0001f4cb Share this Weather"):
                    share_text = (
                        f"\U0001f4cd {display_name} \u00b7 {emoji} {desc} \u00b7 {temp:.0f}\u00b0C "
                        f"(feels {feels:.0f}\u00b0C) \u00b7 Score {score}/100 \u00b7 {slabel} "
                        f"\u2014 via Weather Intelligence"
                    )
                    st.caption("Copy the text below to share \U0001f447")
                    st.text_area("", value=share_text, height=80, key="share_text_area")

    # =========================================================================
    # TAB 2 - 7-DAY FORECAST
    # =========================================================================
    with tab2:
        if not df_daily.empty:
            fig7 = go.Figure()
            fig7.add_trace(go.Bar(
                x=df_daily["day_name"], y=df_daily["rain"],
                name="Rain (mm)", marker_color="rgba(74,144,217,0.35)", yaxis="y2",
            ))
            fig7.add_trace(go.Scatter(
                x=df_daily["day_name"], y=df_daily["max"],
                mode="lines+markers", name="Max \u00b0C",
                line=dict(color="#EF476F", width=3),
                marker=dict(size=8, color="#EF476F"),
            ))
            fig7.add_trace(go.Scatter(
                x=df_daily["day_name"], y=df_daily["min"],
                mode="lines+markers", name="Min \u00b0C",
                line=dict(color="#4A90D9", width=3),
                marker=dict(size=8, color="#4A90D9"),
            ))
            fig7.update_layout(
                **PLOT_LAYOUT_NO_YAXIS,
                title="7-Day Temperature & Precipitation",
                title_font=dict(size=16, color="#1A1A2E"),
                legend=dict(orientation="h", y=1.12),
                yaxis=dict(title="Temperature (\u00b0C)", showgrid=True, gridcolor="#F0F4FF"),
                yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right",
                            showgrid=False, rangemode="tozero"),
                height=380,
            )
            st.plotly_chart(fig7, use_container_width=True)

            # Enhancement 19: Day cards with sparkline precipitation
            cols = st.columns(7)
            for i, row in df_daily.iterrows():
                _, em = wmo_label(row["wcode"])
                rain_val = row["rain"] if row["rain"] is not None else 0
                try:
                    day_str = row["date"].strftime("%Y-%m-%d")
                    spark_vals = []
                    for h in [6, 9, 12, 15, 18, 21]:
                        mask = (
                            (df_hourly["time"].dt.strftime("%Y-%m-%d") == day_str)
                            & (df_hourly["time"].dt.hour == h)
                        )
                        matched = df_hourly[mask]
                        if not matched.empty:
                            v = matched.iloc[0]["precip_prob"]
                            spark_vals.append(float(v) if v is not None else 0.0)
                        else:
                            spark_vals.append(0.0)
                    svg = make_sparkline_svg(spark_vals)
                except Exception:
                    svg = ""
                with cols[i % 7]:
                    st.markdown(
                        f'<div class="day-card">'
                        f'<div class="day-name">{row["day_name"]}</div>'
                        f'<div class="day-emoji">{em}</div>'
                        f'<div class="day-max">{row["max"]:.0f}\u00b0</div>'
                        f'<div class="day-min">{row["min"]:.0f}\u00b0</div>'
                        f'<div class="day-rain">\U0001f327\ufe0f {rain_val:.1f}mm</div>'
                        f'<div style="margin-top:4px;display:flex;justify-content:center;">{svg}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Enhancement 12: Weekly UV Radar chart
            st.markdown("---")
            uv_vals = df_daily["uv"].fillna(0).tolist()
            fig_uv_radar = go.Figure()
            fig_uv_radar.add_trace(go.Scatterpolar(
                r=uv_vals,
                theta=df_daily["day_name"].tolist(),
                fill="toself",
                fillcolor="rgba(255,107,53,0.2)",
                line_color="#FF6B35",
                mode="lines+markers",
                name="UV Index",
            ))
            uv_max = max(max(uv_vals) + 1, 5) if uv_vals else 5
            fig_uv_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, uv_max])),
                paper_bgcolor="white",
                font=dict(color="#1A1A2E"),
                title="\u2600\ufe0f Weekly UV Radar",
                title_font=dict(size=15, color="#1A1A2E"),
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig_uv_radar, use_container_width=True)

            # Enhancement 20: Pack Your Bag checklist
            pack_items = []
            if any((v or 0) > 2   for v in df_daily["rain"].fillna(0)):  pack_items.append("\u2602\ufe0f Umbrella")
            if any((v or 99) < 12 for v in df_daily["min"].fillna(99)):  pack_items.append("\U0001f9e5 Jacket")
            if any((v or 99) < 5  for v in df_daily["min"].fillna(99)):  pack_items.append("\U0001f9e3 Scarf & Gloves")
            if any((v or 99) < 0  for v in df_daily["min"].fillna(99)):  pack_items.append("\u2744\ufe0f Heavy Coat")
            if any((v or 0) > 5   for v in df_daily["uv"].fillna(0)):    pack_items.append("\U0001f576\ufe0f Sunglasses")
            if any((v or 0) > 7   for v in df_daily["uv"].fillna(0)):    pack_items.append("\U0001f9f4 Sunscreen")
            if any((v or 0) > 40  for v in df_daily["wind"].fillna(0)):  pack_items.append("\U0001f45f Trainers")
            if any((v or 0) > 28  for v in df_daily["max"].fillna(0)):   pack_items.append("\U0001f4a7 Water Bottle")

            pill_style = (
                "display:inline-block;background:#E8FBF5;color:#05A87A;"
                "border:1.5px solid #06D6A0;border-radius:999px;"
                "padding:6px 16px;font-size:0.9rem;font-weight:600;margin:4px;"
            )
            if pack_items:
                badges = "".join(f'<span style="{pill_style}">{item}</span>' for item in pack_items)
                pack_html = (
                    '<div class="card">'
                    '<div style="font-size:1rem;font-weight:800;color:#1A1A2E;margin-bottom:10px;">'
                    '\U0001f392 Pack Your Bag</div>'
                    f'{badges}</div>'
                )
            else:
                pack_html = (
                    '<div class="card">'
                    '<div style="font-size:1rem;font-weight:800;color:#1A1A2E;margin-bottom:10px;">'
                    '\U0001f392 Pack Your Bag</div>'
                    '<span style="color:#05A87A;font-weight:600;">'
                    '\u2705 You\'re all set! Perfect conditions ahead.</span></div>'
                )
            st.markdown(pack_html, unsafe_allow_html=True)

    # =========================================================================
    # TAB 3 - HOURLY
    # =========================================================================
    with tab3:
        if not df_24.empty:
            # Enhancement 11: Segmented-colour temperature ribbon
            def _temp_band(t):
                if t < 10:   return "cold",    "#4A90D9", "rgba(74,144,217,0.12)"
                elif t < 18: return "cool",    "#06D6A0", "rgba(6,214,160,0.12)"
                elif t < 24: return "comfort", "#06D6A0", "rgba(6,214,160,0.18)"
                elif t < 30: return "warm",    "#FF6B35", "rgba(255,107,53,0.12)"
                else:        return "hot",     "#EF476F", "rgba(239,71,111,0.12)"

            fig_temp = go.Figure()
            fig_temp.add_hrect(
                y0=18, y1=24,
                fillcolor="rgba(6,214,160,0.08)", line_width=0,
                annotation_text="Comfort zone",
                annotation_position="top left",
                annotation_font=dict(color="#06D6A0", size=11),
            )

            temp_vals = df_24["temp"].fillna(0).tolist()
            time_vals = df_24["time"].tolist()

            if temp_vals:
                groups   = []
                cur_band = _temp_band(temp_vals[0])
                cur_grp  = {"band": cur_band, "times": [time_vals[0]], "temps": [temp_vals[0]]}
                for i in range(1, len(temp_vals)):
                    band = _temp_band(temp_vals[i])
                    if band[0] == cur_band[0]:
                        cur_grp["times"].append(time_vals[i])
                        cur_grp["temps"].append(temp_vals[i])
                    else:
                        groups.append(cur_grp)
                        cur_band = band
                        cur_grp  = {
                            "band":  band,
                            "times": [cur_grp["times"][-1], time_vals[i]],
                            "temps": [cur_grp["temps"][-1], temp_vals[i]],
                        }
                groups.append(cur_grp)
                shown = set()
                for g in groups:
                    bname, lcolor, fcolor = g["band"]
                    fig_temp.add_trace(go.Scatter(
                        x=g["times"], y=g["temps"],
                        mode="lines",
                        name=bname.capitalize(),
                        showlegend=(bname not in shown),
                        line=dict(color=lcolor, width=3, shape="spline"),
                        fill="tozeroy",
                        fillcolor=fcolor,
                    ))
                    shown.add(bname)

            fig_temp.update_layout(
                **PLOT_LAYOUT,
                title="Hourly Temperature \u2014 Next 24h",
                title_font=dict(size=15, color="#1A1A2E"),
                yaxis_title="\u00b0C", height=300,
                legend=dict(orientation="h", y=1.12),
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
                **PLOT_LAYOUT_NO_YAXIS,
                title="Precipitation Probability \u2014 Next 24h",
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
            st.markdown(
                f'<div class="card" style="text-align:center;">'
                f'<div style="font-size:1rem;color:#5A6A8A;font-weight:600;">'
                f'\u23f0 Best Time to Go Outside (Next 12h)</div>'
                f'<div style="font-size:2.4rem;font-weight:900;color:#FF6B35;">{best_time}</div>'
                f'<div style="font-size:1rem;color:#1A1A2E;">'
                f'Expected {best_row["temp"]:.1f}\u00b0C \u00b7 '
                f'{best_row["precip_prob"]:.0f}% rain \u00b7 '
                f'{best_row["wind"]:.0f} km/h wind</div></div>',
                unsafe_allow_html=True,
            )

            # Enhancement 14: Feels-like vs actual temperature
            if "feels_like" in df_24.columns and df_24["feels_like"].notna().any():
                fig_feels = go.Figure()
                fig_feels.add_trace(go.Scatter(
                    x=df_24["time"], y=df_24["temp"],
                    mode="lines", name="Temperature",
                    line=dict(color="#FF6B35", width=3, shape="spline"),
                ))
                fig_feels.add_trace(go.Scatter(
                    x=df_24["time"], y=df_24["feels_like"],
                    mode="lines", name="Feels Like",
                    line=dict(color="#A855F7", width=3, shape="spline"),
                    fill="tonexty",
                    fillcolor="rgba(168,85,247,0.12)",
                ))
                fig_feels.update_layout(
                    **PLOT_LAYOUT,
                    title="\U0001f321\ufe0f Temperature vs. Feels Like \u2014 Next 24h",
                    title_font=dict(size=15, color="#1A1A2E"),
                    yaxis_title="\u00b0C", height=280,
                    legend=dict(orientation="h", y=1.12),
                )
                st.plotly_chart(fig_feels, use_container_width=True)

    # =========================================================================
    # TAB 4 - AIR QUALITY
    # =========================================================================
    with tab4:
        if aq:
            aq_hrly  = aq.get("hourly", {})
            aq_times = pd.to_datetime(aq_hrly.get("time", []))
            aq_aqi   = aq_hrly.get("european_aqi", [])
            aq_pm25  = aq_hrly.get("pm2_5", [])
            aq_pm10  = aq_hrly.get("pm10", [])

            df_aq     = pd.DataFrame({"time": aq_times, "aqi": aq_aqi,
                                      "pm25": aq_pm25,  "pm10": aq_pm10})
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
                if v <= 20: return "\U0001f7e2 Excellent"
                if v <= 40: return "\U0001f7e1 Good"
                if v <= 60: return "\U0001f7e0 Moderate"
                if v <= 80: return "\U0001f534 Poor"
                return "\U0001f7e3 Very Poor"

            def aqi_advice(v):
                if v <= 20: return "Air quality is excellent. Enjoy outdoor activities freely!"
                if v <= 40: return "Air quality is good. Suitable for all outdoor activities."
                if v <= 60: return "Moderate air quality. Sensitive groups should limit prolonged outdoor exertion."
                if v <= 80: return "Poor air quality. Everyone should reduce outdoor activities."
                return "Very poor air quality. Avoid outdoors. Consider wearing a mask."

            a1, a2 = st.columns([1, 2])
            with a1:
                aqi_c = aqi_color(cur_aqi)
                st.markdown(
                    f'<div class="card" style="text-align:center;">'
                    f'<div style="font-size:.9rem;font-weight:700;color:#5A6A8A;letter-spacing:.05em;">EUROPEAN AQI</div>'
                    f'<div class="aqi-badge" style="background:{aqi_c}22;color:{aqi_c};">{cur_aqi:.0f}</div>'
                    f'<div style="font-size:1.3rem;font-weight:800;color:{aqi_c};">{aqi_label(cur_aqi)}</div>'
                    f'<hr class="divider">'
                    f'<div style="font-size:.92rem;color:#1A1A2E;">{aqi_advice(cur_aqi)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.metric("\U0001f52c PM2.5", f"{cur_pm25:.1f} \u00b5g/m\u00b3" if cur_pm25 else "N/A")
                st.metric("\U0001f52c PM10",  f"{cur_pm10:.1f} \u00b5g/m\u00b3" if cur_pm10 else "N/A")

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
                    title="European AQI \u2014 Next 48h",
                    title_font=dict(size=15, color="#1A1A2E"),
                    yaxis_title="AQI", height=260,
                )
                st.plotly_chart(fig_aqi, use_container_width=True)
        else:
            st.warning("Air quality data unavailable for this location.")

    # =========================================================================
    # TAB 5 - MAP
    # =========================================================================
    with tab5:
        precip_p0_map = hr_precip[0] if hr_precip else 0

        # Build 5×5 grid of 25 points ±1.5° around the city (step 0.75° ≈ 83 km).
        # All fetch_current_only calls are cached (ttl=1800 s) so subsequent renders
        # are instant; only the very first load triggers network requests.
        _GRID_STEP = 0.75  # degrees (~83 km at equator)
        offsets = [i * _GRID_STEP for i in range(-2, 3)]   # [-1.5, -0.75, 0, 0.75, 1.5]
        grid_lats, grid_lons, grid_temps, grid_speeds, grid_dirs = [], [], [], [], []
        for dlat in offsets:
            for dlon in offsets:
                glat = round(lat + dlat, 4)
                glon = round(lon + dlon, 4)
                cd = fetch_current_only(glat, glon)
                grid_lats.append(glat)
                grid_lons.append(glon)
                grid_temps.append(cd["temp"])
                grid_speeds.append(cd["wind_speed"])
                grid_dirs.append(cd["wind_dir"])

        fig_map = go.Figure()

        # Enhancement 1: Temperature heatmap layer
        fig_map.add_trace(go.Densitymapbox(
            lat=grid_lats, lon=grid_lons, z=grid_temps,
            colorscale=[[0, "#4A90D9"], [0.5, "#FFD166"], [1, "#FF6B35"]],
            radius=30, opacity=0.5, showscale=True,
            name="Temperature",
        ))

        # Enhancement 2: Wind direction arrows (grouped by speed for colour)
        arrow_chars = [wind_arrow(d) for d in grid_dirs]
        for spd_color, spd_lo, spd_hi, spd_lbl in [
            ("#06D6A0", 0,  20, "Wind <20 km/h"),
            ("#FFD166", 20, 40, "Wind 20-40 km/h"),
            ("#EF476F", 40, 9999, "Wind >40 km/h"),
        ]:
            mask = [spd_lo <= grid_speeds[i] < spd_hi for i in range(len(grid_speeds))]
            if not any(mask):
                continue
            fig_map.add_trace(go.Scattermapbox(
                lat=[grid_lats[i]   for i in range(len(grid_lats))   if mask[i]],
                lon=[grid_lons[i]   for i in range(len(grid_lons))   if mask[i]],
                mode="text",
                text=[arrow_chars[i] for i in range(len(arrow_chars)) if mask[i]],
                textfont=dict(size=18, color=spd_color),
                hovertext=[
                    f"Wind: {grid_speeds[i]:.0f} km/h from {grid_dirs[i]:.0f}\u00b0"
                    for i in range(len(grid_lats)) if mask[i]
                ],
                hoverinfo="text",
                name=spd_lbl,
                showlegend=False,
            ))

        # Enhancement 3: Nearby cities comparison pins
        # fetch_current_only results are cached so these 4 calls are instant after first load
        nearby = find_nearby_cities(lat, lon)
        if nearby:
            nc_lats, nc_lons, nc_labels = [], [], []
            for cname, clat, clon in nearby:
                cdata = fetch_current_only(clat, clon)
                nc_lats.append(clat)
                nc_lons.append(clon)
                nc_labels.append(f"{cname} \u00b7 {cdata['temp']:.0f}\u00b0C")
            fig_map.add_trace(go.Scattermapbox(
                lat=nc_lats, lon=nc_lons,
                mode="markers+text",
                marker=dict(size=12, color="#4A90D9"),
                text=nc_labels,
                textposition="top right",
                name="Nearby Cities",
                showlegend=True,
            ))

        # Enhancement 4: Precipitation radius circle
        # Radius scales with precip probability (0.3 km per %), minimum 5 km
        radius_km = max(5.0, precip_p0_map * 0.3)
        if precip_p0_map < 30:
            circ_color = "rgba(74,144,217,0.25)"
        elif precip_p0_map <= 60:
            circ_color = "rgba(255,209,102,0.30)"
        else:
            circ_color = "rgba(239,71,111,0.35)"
        c_lats, c_lons = circle_points(lat, lon, radius_km)
        fig_map.add_trace(go.Scattermapbox(
            lat=c_lats, lon=c_lons,
            mode="lines",
            fill="toself",
            fillcolor=circ_color,
            line=dict(color=circ_color, width=1),
            name="Precip Radius",
            showlegend=True,
            hoverinfo="skip",
        ))

        # Enhancement 5: Pulse marker (3 concentric rings)
        for pulse_r, pulse_a in [(3, 0.25), (6, 0.15), (9, 0.07)]:
            p_lats, p_lons = circle_points(lat, lon, pulse_r)
            pc = f"rgba(255,107,53,{pulse_a})"
            fig_map.add_trace(go.Scattermapbox(
                lat=p_lats, lon=p_lons,
                mode="lines",
                fill="toself",
                fillcolor=pc,
                line=dict(color=pc, width=1),
                name=f"Pulse {pulse_r}km",
                showlegend=False,
                hoverinfo="skip",
            ))

        # City pin - added LAST so it renders on top
        fig_map.add_trace(go.Scattermapbox(
            lat=[lat], lon=[lon],
            mode="markers+text",
            marker=dict(size=16, color="#FF6B35"),
            text=[f"{display_name} \u00b7 {temp:.0f}\u00b0C {emoji}"],
            textposition="top right",
            name="Your City",
            showlegend=True,
        ))

        fig_map.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=lat, lon=lon),
                zoom=7,
            ),
            paper_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            height=560,
            legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.8)"),
        )
        st.plotly_chart(fig_map, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("\U0001f4cd Latitude",  f"{lat:.4f}\u00b0")
        c2.metric("\U0001f4cd Longitude", f"{lon:.4f}\u00b0")
        c3.metric("\U0001f321\ufe0f Now", f"{temp:.0f}\u00b0C {emoji}")

# === FOOTER =================================================================
st.markdown("""
<div class="footer">
  Data: <a href="https://open-meteo.com" target="_blank">Open-Meteo.com</a> (CC BY 4.0) &middot;
  Geocoding: <a href="https://nominatim.org" target="_blank">Nominatim / OpenStreetMap</a> &middot;
  Built with <a href="https://streamlit.io" target="_blank">Streamlit</a> \U0001f324\ufe0f
</div>
""", unsafe_allow_html=True)
