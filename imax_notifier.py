import asyncio
import os
import requests
from playwright.async_api import async_playwright

TARGET_URL = "https://YOUR_EXACT_SCREENING_URL_HERE"

# We use os.environ so GitHub can inject your passwords secretly later!
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

async def check_ticket():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Checking BFI for tickets...")
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=40000)
        await asyncio.sleep(3)
        
        content = await page.content()
        is_sold_out = "Sold out" in content or "Sold Out" in content
        
        if not is_sold_out:
            msg = f"🚨 TICKET ALERT! Seats may be open for The Odyssey!\nCheck now: {TARGET_URL}"
            print("Ticket found! Sending alert...")
            send_telegram_alert(msg)
        else:
            print("Still sold out. GitHub will check again soon.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_ticket())
