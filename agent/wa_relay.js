/**
 * Tiny HTTP relay for WhatsApp messages.
 * The agent POSTs JSON here, this calls openclaw CLI with proper escaping.
 * Port: 8097
 */
const http = require('http');
const { execSync } = require('child_process');

const PORT = 8097;
const OPENCLAW = String.raw`C:\Users\AI\AppData\Roaming\npm\openclaw.cmd`;

const server = http.createServer((req, res) => {
  if (req.method !== 'POST') {
    res.writeHead(405);
    res.end('Method not allowed');
    return;
  }

  let body = '';
  req.on('data', c => body += c);
  req.on('end', () => {
    try {
      const { target, message, channel } = JSON.parse(body);
      if (!target || !message) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'target and message required' }));
        return;
      }

      // Write message to temp file to avoid shell escaping issues
      const fs = require('fs');
      const os = require('os');
      const path = require('path');
      const tmpFile = path.join(os.tmpdir(), `mrna-wa-${Date.now()}.txt`);
      fs.writeFileSync(tmpFile, message, 'utf-8');

      try {
        // Read from file in PowerShell to preserve newlines
        const cmd = `powershell -NoProfile -Command "$m = Get-Content '${tmpFile}' -Raw; & '${OPENCLAW}' message send --target '${target}' --message $m --channel '${channel || 'whatsapp'}' --json"`;
        const result = execSync(cmd, { timeout: 20000, encoding: 'utf-8', windowsHide: true });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result: result.trim() }));
      } finally {
        try { fs.unlinkSync(tmpFile); } catch {}
      }
    } catch (e) {
      console.error('Send failed:', e.message);
      res.writeHead(500);
      res.end(JSON.stringify({ error: e.message }));
    }
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`WA relay listening on http://127.0.0.1:${PORT}`);
});
