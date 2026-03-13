/**
 * WhatsApp Web Browser Automation Server v2
 * Uses Playwright + Edge to send messages through real WhatsApp Web.
 * 
 * POST /send  { phone, message }
 * GET  /status
 * GET  /qr
 */
const http = require("http");
const { chromium } = require("playwright");
const path = require("path");

const PORT = 8098;
const USER_DATA = path.join(__dirname, "wa_data");

let browser = null;
let page = null;
let ready = false;
let sending = false;  // mutex to prevent concurrent sends
let lastError = "";

async function launchBrowser() {
  console.log("[WA] Launching browser...");
  browser = await chromium.launchPersistentContext(USER_DATA, {
    headless: false,
    channel: "msedge",
    args: ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    viewport: { width: 1280, height: 900 },
  });

  page = browser.pages()[0] || await browser.newPage();
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 60000 });
  console.log("[WA] WhatsApp Web loaded, waiting for login...");

  // Poll for login every 2s for up to 2 minutes
  for (let i = 0; i < 60; i++) {
    if (await isLoggedIn()) {
      ready = true;
      console.log("[WA] Ready! Logged in.");
      return;
    }
    await new Promise(r => setTimeout(r, 2000));
  }
  console.log("[WA] Login timeout. Use /qr to check.");
}

async function isLoggedIn() {
  try {
    // Check for any element that only appears when logged in
    const result = await page.evaluate(() => {
      // Side panel exists when logged in
      const side = document.querySelector("#side");
      if (side) return true;
      // Or check for the search/new chat area
      const app = document.querySelector("#app");
      if (app && app.querySelector("header")) return true;
      // Check for chat list container
      const panes = document.querySelectorAll("[data-testid]");
      for (const p of panes) {
        if (p.getAttribute("data-testid")?.includes("chat")) return true;
      }
      return false;
    });
    return result;
  } catch {
    return false;
  }
}

async function sendMessage(phone, message) {
  // Skip strict ready check — wa.me URL works if session is active

  // Simple mutex
  while (sending) await new Promise(r => setTimeout(r, 500));
  sending = true;

  try {
    const cleanPhone = phone.replace(/[\s\-\+]/g, "");
    console.log(`[WA] Sending to ${cleanPhone} (${message.length} chars)`);

    // Navigate to chat via wa.me URL
    const url = `https://web.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(message)}`;
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });

    // Wait for compose box OR error popup
    let composeFound = false;
    for (let i = 0; i < 20; i++) {
      // Check for compose box
      const compose = await page.evaluate(() => {
        const el = document.querySelector('div[contenteditable="true"][data-tab="10"]')
          || document.querySelector('[data-testid="conversation-compose-box-input"]')
          || document.querySelector('footer div[contenteditable="true"]');
        return !!el;
      });
      if (compose) { composeFound = true; break; }

      // Check for error popup
      const hasError = await page.evaluate(() => {
        const popup = document.querySelector('[data-testid="popup-contents"]');
        return popup ? popup.textContent : null;
      });
      if (hasError) throw new Error(`WhatsApp error: ${hasError}`);

      await new Promise(r => setTimeout(r, 500));
    }

    if (!composeFound) throw new Error("Could not open chat. Number may not be on WhatsApp.");

    // Wait for message to be pre-filled
    await new Promise(r => setTimeout(r, 1500));

    // Click send button or press Enter
    const sent = await page.evaluate(() => {
      const btn = document.querySelector('[data-testid="send"]')
        || document.querySelector('[aria-label="Send"]')
        || document.querySelector('button span[data-icon="send"]')?.parentElement;
      if (btn) { btn.click(); return true; }
      return false;
    });

    if (!sent) {
      await page.keyboard.press("Enter");
    }

    // Wait for delivery
    await new Promise(r => setTimeout(r, 2000));
    console.log(`[WA] Sent to ${cleanPhone}`);
    return { ok: true, phone: cleanPhone, length: message.length };
  } finally {
    sending = false;
  }
}

// ---- HTTP Server ----
const server = http.createServer(async (req, res) => {
  const h = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };

  if (req.method === "GET" && req.url === "/status") {
    if (!ready) ready = await isLoggedIn();
    res.writeHead(200, h);
    res.end(JSON.stringify({ ready, lastError }));
    return;
  }

  if (req.method === "POST" && req.url === "/send") {
    let body = "";
    req.on("data", c => body += c);
    req.on("end", async () => {
      try {
        const { phone, message } = JSON.parse(body);
        if (!phone || !message) { res.writeHead(400, h); res.end('{"ok":false,"error":"phone and message required"}'); return; }
        const result = await sendMessage(phone, message);
        res.writeHead(200, h);
        res.end(JSON.stringify(result));
      } catch (e) {
        lastError = e.message;
        console.error(`[WA] Error: ${e.message}`);
        res.writeHead(500, h);
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404, h);
  res.end('{"error":"not found"}');
});

(async () => {
  try { await launchBrowser(); } catch (e) { console.error(`[WA] Launch failed: ${e.message}`); lastError = e.message; }
  server.listen(PORT, () => console.log(`[WA] Server on http://localhost:${PORT}`));
})();
