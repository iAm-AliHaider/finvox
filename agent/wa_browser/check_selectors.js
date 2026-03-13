/**
 * Quick test: check which selectors exist on the current WhatsApp Web page.
 */
const { chromium } = require("playwright");
const path = require("path");
const USER_DATA = path.join(__dirname, "wa_data");

(async () => {
  const browser = await chromium.launchPersistentContext(USER_DATA, {
    headless: false,
    channel: "msedge",
    viewport: { width: 1280, height: 900 },
  });
  const page = browser.pages()[0] || await browser.newPage();
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 30000 });
  
  // Wait a bit for page to load
  await page.waitForTimeout(8000);

  const selectors = [
    '[aria-label="Search input textbox"]',
    '[data-testid="chat-list"]',
    '[data-testid="chatlist-header"]',
    'div[role="navigation"]',
    '#side',
    'div[data-testid="default-user"]',
    'header',
    '[data-testid="menu-bar-menu"]',
    'canvas[aria-label="Scan this QR code to link a device!"]',
    '[data-testid="qrcode"]',
    'div._aigs',  // side panel
  ];

  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      console.log(`${sel}: ${el ? "FOUND" : "not found"}`);
    } catch (e) {
      console.log(`${sel}: error - ${e.message}`);
    }
  }

  await browser.close();
})();
