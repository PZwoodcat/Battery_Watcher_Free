#!/usr/bin/env python3
"""
Battery_Watcher_Free.py
Minimal background battery watcher

Dependencies:
 - psutil        (pip install psutil)
 - win11toast    (pip install win11toast) [optional]
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Optional, Any

import psutil

# Optional Windows toast
try:
    from win11toast import toast as win11_toast
    HAVE_WIN11TOAST = True
except Exception:
    HAVE_WIN11TOAST = False


# ---------------------------
# Helpers
# ---------------------------
def secs_to_hms(secs: Optional[int]) -> str:
    if secs is None:
        return "unknown"

    if secs in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED):
        return "unknown"

    # Guard against bogus huge values (driver lies)
    if secs > 60 * 60 * 24 * 7:  # > 1 week
        return "no driver estimate"

    mm, ss = divmod(int(secs), 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:d}:{mm:02d}:{ss:02d}"


def check_battery_level(low_threshold: int, high_threshold: int) -> Optional[Dict[str, Any]]:
    bat = psutil.sensors_battery()
    if bat is None:
        print("No battery detected.")
        return None

    percent = int(round(bat.percent))
    plugged = bool(bat.power_plugged)
    human = secs_to_hms(bat.secsleft)

    if not plugged and percent <= low_threshold:
        status = "low"
    elif plugged and percent >= high_threshold:
        status = "high"
    else:
        status = "normal"

    return {
        "status": status,
        "percent": percent,
        "plugged": plugged,
        "time_hms": human,
    }


# ---------------------------
# Telegram
# ---------------------------
def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        print("Telegram HTTP error:", e)
    except Exception as e:
        print("Telegram send failed:", e)

    return False


# ---------------------------
# Windows Toast
# ---------------------------
def send_windows_toast(title: str, msg: str):
    if HAVE_WIN11TOAST:
        try:
            win11_toast(title, msg)
        except Exception as e:
            print("Toast failed:", e)


# ---------------------------
# Main Loop
# ---------------------------
def main():
    LOW_THRESHOLD = 20
    HIGH_THRESHOLD = 85
    POLL_SECONDS = 60

    BOT_TOKEN = "8504017218:AAEQdirPkdctFIh8zwJm2Q3EISrLjcxTl2A"
    CHAT_ID = "779056769" 

    last_status = None
    last_notify = 0

    print("Battery Watcher started...")

    while True:
        info = check_battery_level(LOW_THRESHOLD, HIGH_THRESHOLD)
        if info:
            msg = (
                f"Battery {info['status'].upper()} — "
                f"{info['percent']}% "
                f"(plugged: {info['plugged']}) — "
                f"{info['time_hms']}"
            )

            print(msg)

            if info["status"] != last_status and time.time() - last_notify > 10:
                if BOT_TOKEN and CHAT_ID:
                    send_telegram_message(BOT_TOKEN, CHAT_ID, "🔋 " + msg)

                send_windows_toast("Battery Watcher", msg)
                last_notify = time.time()

            last_status = info["status"]

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
