"""Test: verify dashboard is blurred before OTP verification."""
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

        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        await page.locator("input").first.fill(TEST_PHONE)
        await page.locator("button:has-text('Connect'), button:has-text('Call'), button:has-text('Start')").first.click()
        print("Connected. Checking security gate...")

        # Check at various stages
        for i in range(6):
            await page.wait_for_timeout(5000)
            
            blur_gate = await page.locator("text=Identity Verification Required").count()
            otp_modal = await page.locator("text=Verify Your Identity").count()
            otp_inputs = await page.locator("input[maxlength='1']").count()
            
            print(f"  [{(i+1)*5:2d}s] blur_gate={blur_gate>0} otp_modal={otp_modal>0} otp_inputs={otp_inputs}")
            
            if blur_gate or otp_modal:
                await page.screenshot(path=f"test_screenshots/07_gate_{(i+1)*5}s.png")

        await page.screenshot(path="test_screenshots/08_final_gate.png")
        await browser.close()

asyncio.run(main())
