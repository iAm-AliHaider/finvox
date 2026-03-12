import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto("https://finvox-app.vercel.app", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path="test_screenshots/11_welcome.png")
        await browser.close()

asyncio.run(main())
