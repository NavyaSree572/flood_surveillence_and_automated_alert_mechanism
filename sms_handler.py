import requests
import time
import threading
from queue import Queue
from email_handler import send_email_alert 
from telegram_handler import send_telegram_alert

# --- PROJECT CONFIGURATION ---
GATEWAY_URL = "http://192.168.137.156:8082"
TOKEN = "0b95b02a-d887-4a57-b8ed-af7c07cb09a7"
OFFICER_NUMBERS = ["+919281414357", "+918185998153","+918895008219"]

# 🔥 Queue system (prevents overload)
sms_queue = Queue()

def sms_worker():
    while True:
        data = sms_queue.get()
        if data is None:
            break

        location, lat, lon, count = data

        message = (
            f"🚨 FLOOD ALERT\n"
            f"Loc: {location}\n"
            f"GPS: {lat}, {lon}\n"
            f"People: {count}\n"
            f"STATUS: URGENT"
        )

        headers = {
            "Authorization": TOKEN,
            "Content-Type": "application/json"
        }

        # ==============================
        # 📧 SEND EMAIL
        # ==============================
        try:
            print(f"📧 Sending Email Alert for {location}...")
            send_email_alert(location, lat, lon, count)
        except Exception as e:
            print("❌ Email Trigger Error:", e)

        # ==============================
        # 📲 SEND TELEGRAM (FIXED)
        # ==============================
        try:
            print(f"📲 Sending Telegram Alert for {location}...")
            send_telegram_alert(location, lat, lon, count)
        except Exception as e:
            print("❌ Telegram Trigger Error:", e)

        # ==============================
        # 📩 SEND SMS
        # ==============================
        for number in OFFICER_NUMBERS:
            payload = {"to": number, "message": message}

            try:
                print("\n📡 --- SMS DEBUG START ---")
                print("📨 To:", number)

                response = requests.post(
                    GATEWAY_URL,
                    json=payload,
                    headers=headers,
                    timeout=10
                )

                print("📩 Status:", response.status_code)

                if response.status_code == 200:
                    print("✅ SENT (queued properly)")
                else:
                    print(f"❌ FAILED (Status: {response.status_code})")

                print("📡 --- SMS DEBUG END ---\n")

                # 🔥 Delay between numbers
                time.sleep(3)

            except Exception as e:
                print(f"❌ SMS ERROR: {e}")

        # 🔥 Delay between processing distinct alerts
        time.sleep(5)
        sms_queue.task_done()

# 🔥 Start worker thread
threading.Thread(target=sms_worker, daemon=True).start()

def send_alert_sms(location, lat, lon, count):
    """
    Main function called by tracking_reid.py. 
    It puts the detection into the queue for the worker to process.
    """
    sms_queue.put((location, lat, lon, count))