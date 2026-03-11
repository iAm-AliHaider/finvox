"""Targeted test: check data channel events and OTP modal."""
import asyncio
from playwright.async_api import async_playwright

URL = "https://finvox-app.vercel.app"
TEST_PHONE = "+966551234567"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]
        )
        context = await browser.new_context(permissions=["microphone"])
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # Inject event interceptor BEFORE page loads
        await page.add_init_script("""
            window.__dataChannelEvents = [];
            const origParse = JSON.parse;
            JSON.parse = function(...args) {
                const result = origParse.apply(this, args);
                if (result && result.type && (result.type === 'otp_sent' || result.type === 'call_started' || result.type === 'ui_update')) {
                    window.__dataChannelEvents.push(result);
                    console.log('[DC EVENT]', JSON.stringify(result));
                }
                return result;
            };
        """)

        print(f"Loading {URL}...")
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Fill phone and click connect
        await page.locator("input").first.fill(TEST_PHONE)
        await page.locator("button:has-text('Connect'), button:has-text('Call'), button:has-text('Start')").first.click()
        print("Connected. Waiting for events...")

        # Wait and check periodically
        for i in range(8):
            await page.wait_for_timeout(5000)
            
            events = await page.evaluate("() => window.__dataChannelEvents || []")
            modal_el = await page.query_selector("[class*='otp'], [class*='OTP'], [class*='modal'], [class*='Modal']")
            modal_visible = modal_el is not None
            
            # Also check for the actual OTPModal component
            otp_inputs = await page.locator("input[maxlength='1']").count()
            
            end_btn = await page.locator("button:has-text('End')").count() > 0
            
            print(f"  [{(i+1)*5:2d}s] events={len(events)} modal={modal_visible} otp_inputs={otp_inputs} connected={end_btn}")
            for ev in events:
                print(f"       -> {ev}")

        # Check all console logs for DC events
        dc_logs = [l for l in console_logs if 'DC EVENT' in l]
        print(f"\nData channel events in console: {len(dc_logs)}")
        for l in dc_logs:
            print(f"  {l}")

        # Check for errors
        errors = [l for l in console_logs if l.startswith('[error]')]
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for e in errors:
                print(f"  {e}")

        await page.screenshot(path="test_screenshots/06_dc_test.png")
        await browser.close()

asyncio.run(main())
