"""Test new customer registration flow."""
import asyncio
from playwright.async_api import async_playwright

URL = "https://finvox-app.vercel.app"
NEW_PHONE = "+966500000001"  # Not in DB

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

        # Enter new phone
        await page.locator("input").first.fill(NEW_PHONE)
        
        # Click Go/Connect - for new numbers it should start call
        btn = page.locator("button:has-text('Go'), button:has-text('Connect'), button:has-text('Call'), button:has-text('Start')")
        await btn.first.click()
        print(f"1. Entered {NEW_PHONE}, clicked connect")
        await page.wait_for_timeout(3000)

        # Check what's shown
        for i in range(6):
            await page.wait_for_timeout(5000)
            
            # Check for registration form
            reg_form = await page.locator("text=Your Details").count() > 0
            verify_step = await page.locator("text=Verify Your Phone").count() > 0
            confirm_step = await page.locator("text=Confirm Your Details").count() > 0
            name_input = await page.locator("input[placeholder*='Mohammed']").count() > 0
            progress_steps = await page.locator("div.rounded-full").count()
            
            print(f"  [{(i+1)*5:2d}s] verify={verify_step} details={reg_form} confirm={confirm_step} name_input={name_input}")
            
            if verify_step or reg_form:
                await page.screenshot(path=f"test_screenshots/09_reg_{(i+1)*5}s.png")
                break

        # Final screenshot
        await page.screenshot(path="test_screenshots/10_reg_final.png")
        
        errors = [l for l in console_logs if l.startswith("[error]")]
        if errors:
            print(f"\nErrors: {len(errors)}")
            for e in errors[:5]:
                print(f"  {e}")

        await browser.close()

asyncio.run(main())
