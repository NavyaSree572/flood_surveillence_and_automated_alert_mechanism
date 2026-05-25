import smtplib
from email.mime.text import MIMEText

EMAIL = "kethavathnavyasree@gmail.com"
PASSWORD = "tubt uyju xjnc hbuq"   # ⚠️ app password

TO_EMAILS = [
    "kethavathnavyasree@gmail.com",
    "renuyaswithach@gmail.com",
    "nagurbabu252000@gmail.com"
]

def send_email_alert(location, lat, lon, count):
    subject = "🚨 FLOOD ALERT"
    body = f"""
Flood detected!

Location: {location}
GPS: {lat}, {lon}
People detected: {count}

Take immediate action!
"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL
    msg['To'] = ", ".join(TO_EMAILS)

    try:
        print("🔐 Connecting to Gmail SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("🔑 Logging in...")
        server.login(EMAIL, PASSWORD)

        print("📤 Sending Email...")
        server.sendmail(EMAIL, TO_EMAILS, msg.as_string())

        server.quit()
        print("✅ 📧 Email Sent Successfully!")

    except Exception as e:
        print("❌ Email Error:", e)