"""Browser automation test for MRNA voice agent frontend."""
import asyncio
import json
import time
from playwright.async_api import async_playwright

URL = "https://finvox-app.vercel.app"
TEST_PHONE = "+966551234567"  # Faisal (test customer, not Boss)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            permissions=["microphone"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )
        page = await context.new_page()

        # Collect console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # Collect network requests
        api_calls = []
        page.on("request", lambda req: api_calls.append(req.url) if "/api/" in req.url else None)

        responses = {}
        async def capture_response(response):
            if "/api/" in response.url:
                try:
                    body = await response.text()
                    responses[response.url] = {"status": response.status, "body": body[:500]}
                except:
                    responses[response.url] = {"status": response.status}
        page.on("response", capture_response)

        print(f"1. Loading {URL}...")
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Check page title and content
        title = await page.title()
        print(f"   Title: {title}")

        # Check for MRNA branding
        body_text = await page.inner_text("body")
        has_mrna = "MRNA" in body_text
        print(f"   MRNA branding: {'YES' if has_mrna else 'NO'}")

        # Screenshot initial state
        await page.screenshot(path="test_screenshots/01_initial.png")
        print("   Screenshot: 01_initial.png")

        # Find phone input
        phone_input = page.locator("input[type='tel'], input[placeholder*='phone'], input[placeholder*='Phone'], input[placeholder*='number']")
        count = await phone_input.count()
        if count == 0:
            # Try any text input
            phone_input = page.locator("input[type='text']")
            count = await phone_input.count()
        print(f"2. Phone input found: {count > 0} (count: {count})")

        if count > 0:
            await phone_input.first.fill(TEST_PHONE)
            await page.wait_for_timeout(500)
            print(f"   Entered: {TEST_PHONE}")

            # Find and click the connect/call button
            btn = page.locator("button:has-text('Connect'), button:has-text('Call'), button:has-text('Start')")
            btn_count = await btn.count()
            print(f"3. Connect button found: {btn_count > 0}")

            if btn_count > 0:
                await btn.first.click()
                print("   Clicked connect button")
                await page.wait_for_timeout(3000)
                await page.screenshot(path="test_screenshots/02_connecting.png")

                # Wait for API calls
                print(f"4. API calls made: {len(api_calls)}")
                for url in api_calls:
                    print(f"   - {url}")

                # Check API responses
                for url, resp in responses.items():
                    print(f"   Response {url}: status={resp['status']}")
                    if 'body' in resp:
                        print(f"     Body: {resp['body'][:200]}")

                # Wait for room connection
                print("5. Waiting 10s for room connection...")
                await page.wait_for_timeout(10000)
                await page.screenshot(path="test_screenshots/03_connected.png")

                # Check for OTP modal
                otp_modal = page.locator("[class*='otp'], [class*='OTP'], [data-testid='otp'], div:has-text('verification code')")
                otp_visible = await otp_modal.count() > 0
                print(f"6. OTP modal visible: {otp_visible}")

                # Check for any audio elements
                audio_count = await page.locator("audio").count()
                print(f"7. Audio elements: {audio_count}")

                # Check call state
                end_btn = page.locator("button:has-text('End')")
                end_count = await end_btn.count()
                print(f"8. End Call button visible: {end_count > 0} (means call is active)")

                # Wait more and check console
                await page.wait_for_timeout(5000)
                await page.screenshot(path="test_screenshots/04_after_wait.png")

                # Check for errors
                print(f"\n9. Console logs ({len(console_logs)}):")
                for log in console_logs[-20:]:
                    print(f"   {log}")

                # Check for data channel events in page state
                dc_events = await page.evaluate("""() => {
                    // Check if any global state has events
                    return {
                        documentTitle: document.title,
                        audioElements: document.querySelectorAll('audio').length,
                        hasOTPModal: !!document.querySelector('[class*=otp], [class*=OTP]'),
                    };
                }""")
                print(f"\n10. Page state: {json.dumps(dc_events, indent=2)}")

        print(f"\nDone. Screenshots in test_screenshots/")
        await browser.close()

asyncio.run(main())
