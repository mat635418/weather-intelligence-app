# 🌤️ Weather Intelligence App

> **Actionable weather insights for any city in the world — no API key needed.**

Built with Python & Streamlit, powered by the free [Open-Meteo](https://open-meteo.com) and [OpenStreetMap Nominatim](https://nominatim.org) APIs.

---

## ✨ Features

| Tab | What you get |
|---|---|
| 🌡️ **Now** | Current temp, feels-like, weather score (0–100), activity badges, sunrise/sunset |
| 📅 **7-Day Forecast** | Interactive combo chart (temp lines + rain bars) + 7 daily summary cards |
| 🕐 **Hourly** | 24h temperature area chart with comfort zone, precipitation probability bars, best-time-to-go-out picker |
| 💨 **Air Quality** | AQI gauge, PM2.5/PM10 metrics, 48h AQI bar chart, health advice |
| 🗺️ **Map** | Interactive OpenStreetMap centred on your city with live temperature overlay |

**Design highlights:**
- 🎨 Light-only theme — warm sky blues, sunny yellows, energetic orange
- 📊 All charts built with Plotly (white backgrounds, clean grid lines)
- ⚡ 30-minute API response caching via `@st.cache_data`
- 🌍 Works for any city worldwide
- 🔑 Zero API keys required

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/mat635418/weather-intelligence-app.git
cd weather-intelligence-app

# 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Then open **http://localhost:8501** in your browser. 🎉

---

## 🌐 Deploy for Free (Streamlit Community Cloud)

1. Push this repo to GitHub (already done ✅)
2. Go to **[share.streamlit.io](https://share.streamlit.io)**
3. Click **"New app"**
4. Select:
   - Repository: `mat635418/weather-intelligence-app`
   - Branch: `main`
   - Main file: `app.py`
5. Click **"Deploy"** — your app will be live at a public URL in ~2 minutes!

---

## 🏗️ Project Structure

```
weather-intelligence-app/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Light theme + server config
├── .gitignore
└── README.md
```

---

## 📡 Data Sources

| Source | Data | Cost |
|---|---|---|
| [Open-Meteo](https://open-meteo.com) | Weather forecast, air quality, historical | Free (CC BY 4.0) |
| [Nominatim / OSM](https://nominatim.org) | City geocoding (name → lat/lon) | Free |

No API keys. No rate-limit surprises. No credit card.

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Plotly](https://plotly.com/python/)** — Interactive charts
- **[Pandas](https://pandas.pydata.org)** — Data manipulation
- **[Requests](https://requests.readthedocs.io)** — HTTP calls

---

## 📄 License

MIT — feel free to fork, extend, and deploy your own version.

---

<p align="center">
  Made with ❤️ and ☀️ · Data by <a href="https://open-meteo.com">Open-Meteo</a>
</p>