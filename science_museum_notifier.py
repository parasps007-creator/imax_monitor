import asyncio
import os
import requests
from playwright.async_api import async_playwright

# Science Museum / IMAX link
TARGET_URL = "https://my.sciencemuseum.org.uk/423861/470214"

# Telegram Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 1. Row Filter: Rows C through N
ALLOWED_ROWS = [chr(i) for i in range(ord('C'), ord('N') + 1)] # ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']

# 2. Date Filter: 26 to 30 August
ALLOWED_DATES = ["26 August", "27 August", "28 August", "29 August", "30 August", "26 Aug", "27 Aug", "28 Aug", "29 Aug", "30 Aug"]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

async def check_ticket():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Checking Science Museum IMAX for dates 26-30 August & Rows C-N...")
        await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5) # Wait for page and seating map rendering
        
        content = await page.content()
        
        # Check if the page date matches 26-30 August
        date_matched = any(d.lower() in content.lower() for d in ALLOWED_DATES)
        
        if not date_matched:
            print("Page date is not within 26-30 August. Skipping.")
            await browser.close()
            return

        # Check for overall sold-out status
        if "Sold out" in content or "Sold Out" in content:
            print("Performance is sold out for this date.")
            await browser.close()
            return

        # Query seat elements on the seat map SVG / buttons
        seats = await page.query_selector_all(".seat.available, [data-seat-status='available'], button.seat-available, rect.available, path.available")
        
        matching_seats = []
        
        for seat in seats:
            seat_info = await seat.evaluate("""el => {
                return (el.getAttribute('aria-label') || '') + ' ' + 
                       (el.getAttribute('data-seat-id') || '') + ' ' + 
                       (el.getAttribute('title') || '') + ' ' + 
                       (el.textContent || '');
            }""")
            
            # Check if any allowed row (C-N) is present
            for row in ALLOWED_ROWS:
                if f"Row {row}" in seat_info or f"row-{row.lower()}" in seat_info.lower() or f"{row}-" in seat_info:
                    matching_seats.append(seat_info.strip())
                    break

        if matching_seats:
            found_str = "\n".join(matching_seats[:5])
            msg = f"🚨 SCIENCE MUSEUM TICKET ALERT!\nSeats found between 26-30 August in Rows C-N:\n{found_str}\n\nBook immediately: {TARGET_URL}"
            print(f"Match found!\n{msg}")
            send_telegram_alert(msg)
        else:
            print("No available seats found in Rows C-N for 26-30 August.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_ticket())
