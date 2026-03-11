"""Browser test with fake mic for MRNA agent."""
import asyncio
import json
from playwright.async_api import async_playwright

URL = "https://finvox-app.vercel.app"
TEST_PHONE = "+966551234567"

async def main():
    async with async_playwright() as p:
        # Launch with fake media devices
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                "--allow-file-access",
            ]
        )
        context = await browser.new_context(
            permissions=["microphone"],
        )
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        responses = {}
        async def capture_response(response):
            if "/api/" in response.url:
                try:
                    body = await response.text()
                    responses[response.url.split("?")[0]] = {"status": response.status, "body": body[:300]}
                except:
                    pass
        page.on("response", capture_response)

        print(f"1. Loading {URL}...")
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)
        print(f"   Title: {await page.title()}")

        # Enter phone and connect
        phone_input = page.locator("input")
        await phone_input.first.fill(TEST_PHONE)
        print(f"2. Entered phone: {TEST_PHONE}")

        btn = page.locator("button:has-text('Connect'), button:has-text('Call'), button:has-text('Start')")
        await btn.first.click()
        print("3. Clicked connect")
        await page.wait_for_timeout(3000)

        # Check API responses
        for url, resp in responses.items():
            print(f"   API {url.split('/')[-1]}: {resp['status']}")

        # Wait for room connection and agent greeting
        print("4. Waiting 20s for agent to greet...")
        for i in range(4):
            await page.wait_for_timeout(5000)
            # Check state
            state = await page.evaluate("""() => ({
                audioElements: document.querySelectorAll('audio').length,
                hasOTPModal: !!document.querySelector('[class*=otp], [class*=OTP], [class*=modal]'),
                endBtnVisible: !!document.querySelector('button[class*=red], button:has(span[class*=pulse])'),
                bodyText: document.body.innerText.substring(0, 200),
            })""")
            
            # Check for End Call button (means connected)
            end_btn = page.locator("button:has-text('End')")
            end_visible = await end_btn.count() > 0
            
            print(f"   [{(i+1)*5}s] audio={state['audioElements']} otp_modal={state['hasOTPModal']} end_btn={end_visible}")

        await page.screenshot(path="test_screenshots/05_final.png")

        # Final console logs
        print(f"\n5. Console logs ({len(console_logs)}):")
        for log in console_logs:
            print(f"   {log}")

        await browser.close()

asyncio.run(main())
