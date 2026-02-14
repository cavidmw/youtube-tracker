import os
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import plotly.express as px

HEADERS = ["Tarih", "Toplam Izlenme", "Gunluk Artis", "Abone Sayisi", "Video Sayisi"]

def tr_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def gs_read_df(sheet_id: str) -> pd.DataFrame:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(sheet_id).sheet1

    values = ws.get_all_values()
    if len(values) <= 1:
        return pd.DataFrame(columns=HEADERS)

    df = pd.DataFrame(values[1:], columns=values[0])
    for col in ["Toplam Izlenme", "Gunluk Artis", "Abone Sayisi", "Video Sayisi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    df = df.dropna(subset=["Tarih"]).sort_values("Tarih")
    return df

def inject_css():
    st.markdown("""
    <style>
      .stApp {
        background: radial-gradient(1200px 600px at 10% 10%, rgba(80,120,255,0.25), transparent 60%),
                    radial-gradient(1000px 600px at 90% 20%, rgba(255,80,180,0.20), transparent 55%),
                    radial-gradient(900px 500px at 50% 90%, rgba(80,255,200,0.15), transparent 55%),
                    #0b0f19;
      }
      /* kart görünümü */
      div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 16px 18px;
        backdrop-filter: blur(10px);
      }
      /* kenar boşluklarını azalt (daha az scroll) */
      section.main > div { padding-top: 1.2rem; }
      header { visibility: hidden; height: 0px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_dotenv()
    sheet_id = os.getenv("SHEET_ID")

    st.set_page_config(page_title="YouTube Tracker", layout="wide")
    inject_css()

    st.title("YouTube Shorts Günlük Takip")

    if not sheet_id:
        st.error("SHEET_ID yok. .env dosyanı kontrol et.")
        st.stop()

    df = gs_read_df(sheet_id)
    if df.empty:
        st.info("Sheets boş. Önce `python main.py` çalıştırıp veri ekle.")
        st.stop()

    latest = df.iloc[-1]

    # ÜST KARTLAR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam İzlenme", tr_int(int(latest["Toplam Izlenme"])))
    c2.metric("Günlük Artış", tr_int(int(latest["Gunluk Artis"])))
    c3.metric("Abone", tr_int(int(latest["Abone Sayisi"])))  # yuvarlama yok
    c4.metric("Video", tr_int(int(latest["Video Sayisi"])))

    # SOL MENÜ (seçim)
    st.sidebar.title("Kontrol Paneli")
    metric = st.sidebar.selectbox(
        "Hangi metriği görmek istiyorsun?",
        ["Toplam Izlenme", "Gunluk Artis", "Abone Sayisi", "Video Sayisi"]
    )

    chart_type = st.sidebar.selectbox("Grafik tipi", ["Çizgi", "Bar"])

    title_map = {
        "Toplam Izlenme": "Toplam İzlenme",
        "Gunluk Artis": "Günlük İzlenme Artışı",
        "Abone Sayisi": "Abone Sayısı",
        "Video Sayisi": "Video Sayısı",
    }

    # TEK GRAFİK: seçtiğin metrik
    if chart_type == "Çizgi":
        fig = px.line(df, x="Tarih", y=metric, title=title_map[metric], markers=True)
    else:
        fig = px.bar(df, x="Tarih", y=metric, title=title_map[metric])

    fig.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
