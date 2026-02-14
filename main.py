import os
from datetime import datetime, timezone

import requests
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


HEADERS = ["Tarih", "Toplam Izlenme", "Gunluk Artis", "Abone Sayisi", "Video Sayisi"]


def get_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Eksik ENV: {name} (.env dosyasına ekle)")
    return v


def yt_channel_stats(api_key: str, channel_id: str) -> dict:
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "statistics", "id": channel_id, "key": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    items = r.json().get("items", [])
    if not items:
        raise RuntimeError("Kanal bulunamadı. CHANNEL_ID doğru mu?")

    s = items[0]["statistics"]
    return {
        "views": int(s.get("viewCount", 0)),
        "subs": int(s.get("subscriberCount", 0)),
        "videos": int(s.get("videoCount", 0)),
    }


def open_sheet(sheet_id: str):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open_by_key(sheet_id).sheet1


def ensure_headers(ws):
    row1 = ws.row_values(1)
    if row1 != HEADERS:
        ws.clear()
        ws.append_row(HEADERS)


def last_total_views(ws):
    values = ws.get_all_values()
    if len(values) <= 1:
        return None
    last = values[-1]
    try:
        return int(str(last[1]).replace(".", "").replace(",", "").strip())
    except Exception:
        return None


def append_today(ws, total_views: int, subs: int, videos: int):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prev = last_total_views(ws)

    daily = 0 if prev is None else (total_views - prev)

    # EKSİ günlük artış olmasın (YouTube bazen düzeltme yapar)
    if daily < 0:
        daily = 0

    row = [today, int(total_views), int(daily), int(subs), int(videos)]
    ws.append_row(row, value_input_option="USER_ENTERED")
    print("Eklendi:", row)


def main():
    load_dotenv()
    api_key = get_env("YT_API_KEY")
    sheet_id = get_env("SHEET_ID")
    channel_id = os.getenv("CHANNEL_ID", "UCp1X8MWFdDSRAn6bvo6qiCg")

    stats = yt_channel_stats(api_key, channel_id)
    ws = open_sheet(sheet_id)
    ensure_headers(ws)
    append_today(ws, stats["views"], stats["subs"], stats["videos"])


if __name__ == "__main__":
    main()
