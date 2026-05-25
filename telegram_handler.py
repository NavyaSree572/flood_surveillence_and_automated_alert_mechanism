import requests

# 🔑 Paste your NEW token here
BOT_TOKEN = "8483740372:AAEPkU25vZyIjniWVNKfu1rl7PC8kNweebU"

# 👤 Paste your chat ID here
CHAT_ID = "-5156066974"

def send_telegram_alert(location, lat, lon, count):
    message = f"""
🚨 FLOOD ALERT 🚨

📍 Location: {location}
🌐 GPS: {lat}, {lon}
👥 People Detected: {count}

⚠️ Take Immediate Action!
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print("📲 Telegram Status:", response.status_code)

        if response.status_code == 200:
            print("✅ Telegram Sent Successfully")
        else:
            print("❌ Telegram Failed")

    except Exception as e:
        print("❌ Telegram Error:", e)