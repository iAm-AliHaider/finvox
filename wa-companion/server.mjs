/**
 * MRNA WhatsApp Companion
 * - Sends OTPs for voice agent verification
 * - Sends post-call summaries
 * - Handles inbound customer messages (text support)
 * - Delivers statements and documents
 */
import express from "express";
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const require = createRequire(import.meta.url);
const pkg = require("@whiskeysockets/baileys");
const makeWASocket = pkg.default;
const { 
  useMultiFileAuthState, 
  DisconnectReason, 
  fetchLatestBaileysVersion, 
  makeInMemoryStore 
} = pkg;

const Database = require("better-sqlite3");
const pino = require("pino");

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// â”€â”€â”€ Setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const PORT = process.env.WA_PORT || 8087;
const AUTH_DIR = path.join(__dirname, "auth");
const DB_PATH = path.join(__dirname, "data", "wa.db");

fs.mkdirSync(AUTH_DIR, { recursive: true });
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const db = new Database(DB_PATH);
db.exec(`
  CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    direction TEXT NOT NULL,
    type TEXT DEFAULT 'text',
    content TEXT,
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent'
  );
  CREATE TABLE IF NOT EXISTS sessions (
    phone TEXT PRIMARY KEY,
    customer_name TEXT,
    last_message TEXT,
    last_at TEXT DEFAULT CURRENT_TIMESTAMP
  );
`);

const logger = pino({ level: "warn" });
let sock = null;
let waStatus = "disconnected";
let qrCode = null;

// â”€â”€â”€ WhatsApp Connection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function connectWA() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    generateHighQualityLinkPreview: false,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      qrCode = qr;
      waStatus = "qr";
      console.log("[WA] QR code ready â€” scan via /qr endpoint");
    }
    if (connection === "open") {
      waStatus = "connected";
      qrCode = null;
      console.log("[WA] Connected to WhatsApp");
    }
    if (connection === "close") {
      waStatus = "disconnected";
      const code = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = code !== DisconnectReason.loggedOut;
      if (shouldReconnect) {
        console.log("[WA] Reconnecting...");
        setTimeout(connectWA, 5000);
      } else {
        console.log("[WA] Logged out â€” delete auth/ and restart");
      }
    }
  });

  // Handle inbound messages from customers
  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;
    for (const msg of messages) {
      if (msg.key.fromMe) continue;
      const phone = msg.key.remoteJid?.replace("@s.whatsapp.net", "").replace(/@.+$/, "");
      if (!phone) continue;

      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        "";

      if (!text) continue;

      console.log(`[WA] Inbound from ${phone}: ${text.slice(0, 60)}`);
      db.prepare(
        "INSERT INTO messages (phone, direction, content) VALUES (?,?,?)"
      ).run(phone, "inbound", text);
      db.prepare(
        "INSERT OR REPLACE INTO sessions (phone, last_message, last_at) VALUES (?,?,CURRENT_TIMESTAMP)"
      ).run(phone, text);

      // Auto-reply (basic)
      await handleInboundMessage(phone, text);
    }
  });
}

// â”€â”€â”€ Inbound Message Handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function handleInboundMessage(phone, text) {
  const lower = text.toLowerCase().trim();

  // Keywords for self-service
  if (lower === "hi" || lower === "hello" || lower === "Ù…Ø±Ø­Ø¨Ø§") {
    await sendMessage(phone,
      `Welcome to *MRNA Financial Services* ðŸ‘‹\n\n` +
      `I can help you with:\n` +
      `â€¢ *balance* â€” Check your loan balance\n` +
      `â€¢ *portfolio* â€” Check investment value\n` +
      `â€¢ *emi* â€” Next EMI due date\n` +
      `â€¢ *statement* â€” Request account statement\n` +
      `â€¢ *agent* â€” Talk to an agent\n\n` +
      `Or call us for a full voice consultation.`
    );
    return;
  }

  if (lower.includes("agent") || lower.includes("human") || lower.includes("help")) {
    await sendMessage(phone,
      `I\'ll connect you with your relationship manager.\n` +
      `They will call you back within 2 hours.\n\n` +
      `Reference: WA-${Date.now().toString().slice(-6)}`
    );
    return;
  }

  if (lower.includes("statement") || lower.includes("report")) {
    await sendMessage(phone,
      `Your account statement request has been received. âœ…\n` +
      `It will be generated and sent to this WhatsApp within 10 minutes.`
    );
    return;
  }

  // Default
  await sendMessage(phone,
    `Thank you for contacting MRNA. ðŸ¦\n\n` +
    `For account queries, please call our voice agent or reply with:\n` +
    `*hi* â€” Main menu\n` +
    `*agent* â€” Connect to relationship manager`
  );
}

// â”€â”€â”€ Send Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function sendMessage(phone, text) {
  if (waStatus !== "connected") {
    console.warn(`[WA] Not connected â€” cannot send to ${phone}`);
    return { success: false, error: "not connected" };
  }

  // Normalize phone
  const jid = phone.startsWith("+") ? `${phone.slice(1)}@s.whatsapp.net` : `${phone}@s.whatsapp.net`;

  try {
    await sock.sendMessage(jid, { text });
    db.prepare("INSERT INTO messages (phone, direction, content) VALUES (?,?,?)").run(phone, "outbound", text);
    return { success: true };
  } catch (e) {
    console.error(`[WA] Send error: ${e.message}`);
    return { success: false, error: e.message };
  }
}

async function sendOTP(phone, code, customerName) {
  const message =
    `ðŸ” *MRNA Security Code*\n\n` +
    `Hello ${customerName || ""},\n\n` +
    `Your verification code is:\n\n` +
    `*${code}*\n\n` +
    `Valid for 5 minutes. Do NOT share this code.\n` +
    `If you didn't request this, contact us immediately.`;

  return sendMessage(phone, message);
}

async function sendCallSummary(phone, customerName, summary) {
  const message =
    `ðŸ“‹ *Call Summary â€” MRNA*\n\n` +
    `Hello ${customerName},\n\n` +
    `${summary}\n\n` +
    `For queries, reply to this message or call us.\n` +
    `_MRNA Financial Services_`;

  return sendMessage(phone, message);
}

async function sendStatement(phone, customerName, statementType) {
  const message =
    `ðŸ“„ *${statementType} Statement*\n\n` +
    `Hello ${customerName},\n\n` +
    `Your ${statementType.toLowerCase()} statement has been generated.\n\n` +
    `[Statement would be attached as PDF here]\n\n` +
    `_Generated by MRNA on ${new Date().toLocaleDateString()}_`;

  return sendMessage(phone, message);
}

// â”€â”€â”€ Express API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const app = express();
app.use(express.json());

// CORS
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  next();
});

app.get("/health", (req, res) => {
  res.json({ status: waStatus, qr: !!qrCode });
});

// Raw QR data endpoint (for client-side rendering)
app.get("/qr-data", (req, res) => {
  res.json({ qr: qrCode, status: waStatus });
});

// QR scan page - self-refreshing HTML with client-side QR rendering
app.get("/qr", (req, res) => {
  res.setHeader("Content-Type", "text/html");
  res.send(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MRNA WhatsApp Setup</title>
  <script src="https://cdn.jsdelivr.net/npm/qrcode/build/qrcode.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; background: #f0f4ff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
    .card { background: white; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.12); max-width: 380px; width: 90%; }
    .logo { width: 56px; height: 56px; background: #2563eb; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
    h1 { font-size: 22px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
    .subtitle { color: #666; font-size: 14px; margin-bottom: 24px; }
    #qr-wrap { min-height: 260px; display: flex; align-items: center; justify-content: center; }
    canvas { border-radius: 12px; }
    .status { margin-top: 20px; padding: 10px 18px; border-radius: 99px; font-size: 13px; font-weight: 600; display: inline-block; }
    .status.qr { background: #fff3cd; color: #856404; }
    .status.connected { background: #d1fae5; color: #065f46; }
    .status.disconnected { background: #fee2e2; color: #991b1b; }
    .hint { color: #999; font-size: 12px; margin-top: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">
      <svg width="28" height="28" fill="white" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.37 5.07L2 22l5.09-1.34A9.93 9.93 0 0 0 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm4.64 13.11c-.2.56-.99 1.02-1.6 1.16-.43.1-.99.17-2.87-.62-2.41-1.01-3.96-3.47-4.08-3.63-.12-.16-.98-1.31-.98-2.5 0-1.19.62-1.77.84-2.01.22-.24.48-.3.64-.3h.46c.15 0 .35-.06.55.42.2.48.68 1.67.74 1.79.06.12.1.26.02.41-.08.15-.12.24-.24.38-.12.14-.25.31-.36.42-.12.12-.24.25-.1.49.14.24.62 1.02 1.33 1.65.91.81 1.68 1.06 1.92 1.18.24.12.38.1.52-.06.14-.16.6-.7.76-.94.16-.24.32-.2.54-.12.22.08 1.4.66 1.64.78.24.12.4.18.46.28.06.1.06.56-.14 1.12z"/></svg>
    </div>
    <h1>MRNA WhatsApp</h1>
    <p class="subtitle">Scan with WhatsApp to connect OTP and messaging</p>
    <div id="qr-wrap"><p style="color:#999">Loading...</p></div>
    <div id="status-badge" class="status">Checking...</div>
    <p class="hint" id="hint">Auto-refreshes every 5 seconds</p>
  </div>
  <script>
    async function refresh() {
      try {
        const res = await fetch('/qr-data');
        const { qr, status } = await res.json();
        const badge = document.getElementById('status-badge');
        const wrap = document.getElementById('qr-wrap');
        const hint = document.getElementById('hint');
        badge.className = 'status ' + (status || 'disconnected');
        badge.textContent = status === 'qr' ? 'Scan QR Code' : status === 'connected' ? 'Connected!' : 'Disconnected';
        if (status === 'connected') {
          wrap.innerHTML = '<div style="font-size:64px">✅</div><p style="margin-top:12px;font-weight:600;color:#065f46">WhatsApp Connected!</p>';
          hint.textContent = 'OTP delivery is active';
        } else if (qr) {
          const canvas = document.createElement('canvas');
          wrap.innerHTML = '';
          wrap.appendChild(canvas);
          await QRCode.toCanvas(canvas, qr, { width: 260, margin: 2, color: { dark: '#000', light: '#fff' } });
          hint.textContent = 'Open WhatsApp > Linked Devices > Link a device';
        } else {
          wrap.innerHTML = '<p style="color:#999;padding:40px">Waiting for QR code...</p>';
        }
      } catch(e) {
        document.getElementById('qr-wrap').innerHTML = '<p style="color:#e11d48">Error: ' + e.message + '</p>';
      }
    }
    refresh();
    setInterval(refresh, 5000);
  </script>
</body>
</html>`);
});

// Send OTP (called by voice agent)
app.post("/otp", async (req, res) => {
  const { phone, code, customer_name } = req.body;
  if (!phone || !code) return res.status(400).json({ error: "phone and code required" });
  const result = await sendOTP(phone, code, customer_name || "");
  res.json(result);
});

// Send call summary (called after call ends)
app.post("/summary", async (req, res) => {
  const { phone, customer_name, summary } = req.body;
  if (!phone || !summary) return res.status(400).json({ error: "phone and summary required" });
  const result = await sendCallSummary(phone, customer_name || "Customer", summary);
  res.json(result);
});

// Send statement notification
app.post("/statement", async (req, res) => {
  const { phone, customer_name, statement_type } = req.body;
  if (!phone) return res.status(400).json({ error: "phone required" });
  const result = await sendStatement(phone, customer_name || "Customer", statement_type || "Account");
  res.json(result);
});

// Send custom message
app.post("/send", async (req, res) => {
  const { phone, message } = req.body;
  if (!phone || !message) return res.status(400).json({ error: "phone and message required" });
  const result = await sendMessage(phone, message);
  res.json(result);
});

// Message history
app.get("/messages/:phone", (req, res) => {
  const msgs = db.prepare(
    "SELECT * FROM messages WHERE phone = ? ORDER BY sent_at DESC LIMIT 50"
  ).all(req.params.phone);
  res.json(msgs);
});

// Sessions list
app.get("/sessions", (req, res) => {
  const sessions = db.prepare("SELECT * FROM sessions ORDER BY last_at DESC").all();
  res.json(sessions);
});

// â”€â”€â”€ Start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

app.listen(PORT, () => {
  console.log(`[WA Companion] API on port ${PORT}`);
  connectWA();
});



