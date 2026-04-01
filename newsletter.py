import smtplib
import requests
import schedule
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ─── 설정 ───────────────────────────────────────
GENSPARK_API_KEY = os.environ.get("GENSPARK_API_KEY", "")
GMAIL_ADDRESS    = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PW     = os.environ.get("GMAIL_APP_PW", "")
TO_EMAIL         = os.environ.get("TO_EMAIL", "")

print(f"✅ 환경변수 확인:")
print(f"   GMAIL_ADDRESS: {GMAIL_ADDRESS}")
print(f"   TO_EMAIL: {TO_EMAIL}")
print(f"   GENSPARK_API_KEY: {'설정됨' if GENSPARK_API_KEY else '없음'}")
print(f"   GMAIL_APP_PW: {'설정됨' if GMAIL_APP_PW else '없음'}")

# ─── 뉴스레터 초안 생성 ──────────────────────────
def generate_newsletter():
    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"""오늘은 {today}입니다.
브랜드 경험 설계(BX) 뉴스레터 'BX브리프' 에디터로서,
오늘 날짜 기준 브랜드 경험, 퍼스널 브랜딩, 경험 마케팅 관련
국내외 최신 뉴스 3가지를 웹에서 검색해서 아래 형식으로 정리해줘.
중요도 순으로 정렬하고, 1인 브랜더/컨설턴트/크리에이터 관점 인사이트 포함.

---
📌 뉴스 제목:
📊 핵심 내용 (2줄 이내):
💡 브랜드빌더에게 미치는 영향 (1줄):
🔗 출처:
---

뉴스 3개 작성 후 마지막에
✍️ 에디터 한마디 (3줄 이내): 도 추가해줘."""

    print("📡 Genspark API 호출 중...")
    response = requests.post(
        "https://api.genspark.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GENSPARK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "genspark-reasoning-search",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        },
        timeout=60
    )

    print(f"📡 Genspark 응답 코드: {response.status_code}")
    data = response.json()
    return data["choices"][0]["message"]["content"]

# ─── Gmail 발송 ──────────────────────────────────
def send_email(content):
    today = datetime.now().strftime("%Y.%m.%d")
    subject = f"[BX브리프 초안] {today} 뉴스레터 — 검토 후 Stibee 발송해주세요"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = TO_EMAIL

    text_body = f"""BX브리프 주간 초안입니다.
검토 후 Stibee에 붙여넣어 발송해주세요.

{'='*50}
{content}
{'='*50}

이 메일은 Railway에서 매주 월요일 오전 7시에 자동 발송됩니다.
"""

    html_content = content.replace('\n', '<br>')
    html_body = f"""
<html>
<body style="font-family: Georgia, serif; max-width: 680px; margin: 0 auto; padding: 40px 20px; background: #f5f0e8; color: #0d0d0d;">
  <div style="border-bottom: 3px solid #0d0d0d; padding-bottom: 20px; margin-bottom: 30px;">
    <h1 style="font-size: 2rem; margin: 0;">BX브리프</h1>
    <p style="color: #7a7265; font-size: 0.8rem; margin: 5px 0 0;">브랜드 경험 설계 뉴스레터 · {today} 초안</p>
  </div>
  <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px 20px; border-radius: 4px; margin-bottom: 30px;">
    <strong>✏️ 검토 필요</strong> — 아래 내용 확인 후 Stibee에 붙여넣어 발송해주세요.
  </div>
  <div style="line-height: 1.9; font-size: 0.95rem;">{html_content}</div>
  <div style="border-top: 1px solid #d4cfc4; margin-top: 40px; padding-top: 20px; color: #7a7265; font-size: 0.75rem;">
    Railway에서 매주 월요일 오전 7시 자동 발송
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"📧 Gmail 발송 중... {GMAIL_ADDRESS} → {TO_EMAIL}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PW)
        server.sendmail(GMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    print(f"✅ 발송 완료!")

# ─── 메인 실행 ───────────────────────────────────
def run_newsletter():
    print(f"🚀 뉴스레터 생성 시작: {datetime.now()}")
    try:
        content = generate_newsletter()
        print("✅ 초안 생성 완료")
        send_email(content)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

# 매주 월요일 오전 7시 실행
schedule.every().monday.at("07:00").do(run_newsletter)

# RUN_NOW=true 이면 즉시 실행
run_now = os.environ.get("RUN_NOW", "").strip().lower()
print(f"⏰ 스케줄러 시작 — 매주 월요일 07:00 자동 실행")
print(f"🔍 RUN_NOW 값: '{run_now}'")

if run_now == "true":
    print("🧪 즉시 테스트 실행!")
    run_newsletter()

while True:
    schedule.run_pending()
    time.sleep(60)
