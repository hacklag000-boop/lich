import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

# ===== CẤU HÌNH =====
USERNAME = "051207018077"
PASSWORD = "18022007"
BOT_TOKEN = "6128053650:AAErxGFjyvHZxo3zoFHaLAiZyh10dmieFyc"
CHAT_ID = "5373445358"
BASE_URL = "https://courses.ut.edu.vn"
CHECK_INTERVAL = 3600  # giây

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== LOGIN MOODLE =====
def login():
    try:
        res = session.get(f"{BASE_URL}/login/index.php")
        soup = BeautifulSoup(res.text, "html.parser")
        token = soup.find("input", {"name":"logintoken"})
        logintoken = token["value"] if token else ""
        payload = {"username":USERNAME,"password":PASSWORD,"logintoken":logintoken}
        res = session.post(f"{BASE_URL}/login/index.php", data=payload)
        if "loginerrors" in res.text.lower():
            print("❌ Đăng nhập thất bại")
            return False
        print("✅ Đăng nhập thành công")
        return True
    except Exception as e:
        print("❌ Lỗi login:", e)
        return False

# ===== LẤY LỊCH MOODLE =====
def get_calendar(days_ahead=2):
    events = []
    now = datetime.now()
    limit_ts = now.timestamp() + days_ahead*24*3600
    weekday_map = {"Monday":"Thứ 2","Tuesday":"Thứ 3","Wednesday":"Thứ 4",
                   "Thursday":"Thứ 5","Friday":"Thứ 6","Saturday":"Thứ 7","Sunday":"Chủ nhật"}

    for month_offset in [0,1]:
        t = time.localtime(now.timestamp())
        new_month = t.tm_mon + month_offset
        new_year = t.tm_year
        if new_month > 12:
            new_month -= 12
            new_year += 1
        first_day = time.mktime((new_year,new_month,1,0,0,0,0,0,-1))
        url = f"{BASE_URL}/calendar/view.php?view=month&time={int(first_day)}"
        try:
            res = session.get(url)
            soup = BeautifulSoup(res.text,"html.parser")
        except:
            continue

        for td in soup.select("td.day"):
            ts = td.get("data-day-timestamp")
            if not ts: continue
            ts = int(ts)
            if ts < now.timestamp() or ts > limit_ts: continue

            day_number = td.select_one(".day-number")
            day_text = day_number.get_text(strip=True) if day_number else ""
            date = datetime.fromtimestamp(ts).strftime("%d/%m/%Y")

            for e in td.select("a[data-action='view-event']"):
                name = e.get_text(" ",strip=True)
                href = e.get("href","")
                link = href if href.startswith("http") else BASE_URL+href

                # Chi tiết sự kiện
                dates_info = ""
                try:
                    detail_res = session.get(link)
                    detail_soup = BeautifulSoup(detail_res.text,"html.parser")
                    dates_div = detail_soup.select_one("div.activity-dates")
                    if dates_div:
                        lines = dates_div.get_text("\n",strip=True).split("\n")
                        for line in lines:
                            line = line.strip()
                            if not line or ":" not in line:
                                continue
                            dates_info += line + " | "
                except:
                    pass

                msg = f"🗓 Ngày: {date} (Ngày {day_text}) | 📌 Nội dung: {name} | {dates_info}🔗 {link}"
                event_hash = hashlib.md5(msg.encode('utf-8')).hexdigest()
                events.append({"ts":ts,"msg":msg,"hash":event_hash})

    events.sort(key=lambda x:x["ts"])
    return events

# ===== MAIN LOOP =====
if not login():
    exit()

sent_hashes = set()

while True:
    try:
        events = get_calendar(days_ahead=2)
        # Nếu session hết hạn, thử login lại
        if not events:
            print("⚠️ Không lấy được sự kiện, đăng nhập lại...")
            login()
            time.sleep(5)
            continue

        new_events = 0
        for ev in events:
            if ev["hash"] not in sent_hashes:
                send_telegram(ev["msg"])
                sent_hashes.add(ev["hash"])
                new_events += 1

        if new_events == 0:
            print("⚠️ Không có lịch mới")

        print(f"⏳ Kiểm tra xong. Chờ {CHECK_INTERVAL} giây...")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print("❌ Lỗi:", e)
        login()
        time.sleep(10)
