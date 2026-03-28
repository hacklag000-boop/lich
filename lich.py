import time
import requests
from bs4 import BeautifulSoup

# ===== CONFIG =====
USERNAME = "051207018077"
PASSWORD = "18022007"

BOT_TOKEN = "6128053650:AAErxGFjyvHZxo3zoFHaLAiZyh10dmieFyc"
CHAT_ID = "5373445358"

BASE_URL = "https://courses.ut.edu.vn"
CHECK_INTERVAL = 60

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ===== LOGIN =====
def login():
    print("🔐 Login...")

    res = session.get(f"{BASE_URL}/login/index.php")
    soup = BeautifulSoup(res.text, "html.parser")

    token = soup.find("input", {"name": "logintoken"})
    logintoken = token["value"] if token else ""

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "logintoken": logintoken
    }

    res = session.post(f"{BASE_URL}/login/index.php", data=payload)

    if "loginerrors" in res.text.lower():
        print("❌ Login fail")
        return False

    print("✅ Login OK")
    return True

def get_calendar():
    url = f"{BASE_URL}/calendar/view.php?view=month"
    res = session.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    events = []

    now = int(time.time())

    # duyệt qua từng ô ngày
    for td in soup.select("td.day"):
        timestamp = td.get("data-day-timestamp")
        if not timestamp:
            continue

        ts = int(timestamp)
        # chỉ lấy ngày trong vòng 2 ngày tới
        if ts < now or ts > now + 2*24*3600:
            continue

        date = time.strftime("%d/%m/%Y", time.localtime(ts))
        content = td.get_text(" ", strip=True)

        # bỏ qua nếu không có sự kiện
        if not content or "Không có sự kiện" in content:
            continue

        msg = f"""🗓 Ngày: {date}
📌 Nội dung: {content}"""
        events.append(msg)

    # chỉ lấy tối đa 5 sự kiện
    return events[:5]

# ===== MAIN =====
if not login():
    exit()

sent = set()

while True:
    try:
        events = get_calendar()

        if events:
            for ev in events:
                if ev not in sent:
                    send_telegram(ev)
                    sent.add(ev)
        else:
            print("⚠️ Không có event")

        print("⏳ Checking...")

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("❌ Lỗi:", e)
        login()
        time.sleep(10)