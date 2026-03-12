"""Test features 1-7: transcript, OTP verified state, PII masking, tool calls."""
import asyncio
import json
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

        # Inject DC event interceptor
        await page.add_init_script("""
            window.__dcEvents = [];
            const origParse = JSON.parse;
            JSON.parse = function(...args) {
                const result = origParse.apply(this, args);
                if (result && result.type) {
                    window.__dcEvents.push({...result, _ts: Date.now()});
                }
                return result;
            };
        """)

        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # Screenshot welcome page
        await page.screenshot(path="test_screenshots/12_welcome_final.png")

        # Enter phone and look up
        await page.locator("input[placeholder*='+966']").first.fill(TEST_PHONE)
        await page.locator("button:has-text('Look Up')").first.click()
        await page.wait_for_timeout(3000)

        # Check if we got to dashboard
        blur_gate = await page.locator("text=Identity Verification Required").count() > 0
        print(f"1. Security gate (blur): {blur_gate}")
        await page.screenshot(path="test_screenshots/13_blur_gate.png")

        # Wait for agent events
        print("2. Waiting for agent events (30s)...")
        for i in range(6):
            await page.wait_for_timeout(5000)
            events = await page.evaluate("() => window.__dcEvents || []")
            
            event_types = [e.get("type") for e in events]
            transcript_count = event_types.count("transcript")
            tool_calls = [e for e in events if e.get("type") == "tool_call"]
            otp_verified = "otp_verified" in event_types
            
            print(f"  [{(i+1)*5:2d}s] events={len(events)} transcript={transcript_count} tools={len(tool_calls)} verified={otp_verified}")
            
            # Check for masked PII in transcripts
            transcripts = [e for e in events if e.get("type") == "transcript"]
            for t in transcripts[-2:]:
                text = t.get("text", "")[:80]
                has_pii_mask = "****" in text or "***OTP***" in text
                print(f"       {t.get('role','?')}: {text}{'  [PII MASKED]' if has_pii_mask else ''}")

        # Final state
        events = await page.evaluate("() => window.__dcEvents || []")
        event_types = [e.get("type") for e in events]
        
        print(f"\n3. Summary:")
        print(f"   Total events: {len(events)}")
        print(f"   Event types: {set(event_types)}")
        print(f"   Transcript messages: {event_types.count('transcript')}")
        print(f"   Tool calls: {event_types.count('tool_call')}")
        print(f"   OTP verified: {'otp_verified' in event_types}")
        print(f"   Call started: {'call_started' in event_types}")
        print(f"   OTP sent: {'otp_sent' in event_types}")

        await page.screenshot(path="test_screenshots/14_features_final.png")
        await browser.close()

asyncio.run(main())

