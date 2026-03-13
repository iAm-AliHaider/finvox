/**
 * WA Relay v5 - Uses OpenClaw's internal createDefaultDeps + send logic.
 * Loads the OpenClaw config, creates deps, and sends via the Baileys connection.
 * Port: 8097
 */
const http = require('http');
const path = require('path');

const PORT = 8097;
const OC_PATH = path.join(process.env.APPDATA, 'npm', 'node_modules', 'openclaw');

let sendDeps = null;
let ocConfig = null;

async function initOpenClaw() {
  try {
    const oc = require(OC_PATH);
    ocConfig = oc.loadConfig();
    sendDeps = oc.createDefaultDeps(ocConfig);
    console.log('OpenClaw deps loaded');
    return true;
  } catch (e) {
    console.error('OpenClaw init failed:', e.message);
    return false;
  }
}

// Alternative: use the reply module directly
async function sendViaOC(target, message, channel = 'whatsapp') {
  try {
    // Try to find and use the send function from openclaw internals
    const replyMod = require(path.join(OC_PATH, 'dist', 'reply-Cx57rl6c.js'));
    
    // Check what's exported
    const keys = Object.keys(replyMod).filter(k => 
      k.toLowerCase().includes('send') || 
      k.toLowerCase().includes('outbound') ||
      k.toLowerCase().includes('message')
    );
    console.log('Reply module send-related exports:', keys.slice(0, 10));
    
    return { error: 'Not yet implemented - checking exports' };
  } catch (e) {
    return { error: e.message };
  }
}

// Fallback: Use child_process with proper escaping  
const { spawn } = require('child_process');

function sendViaCLI(target, message, channel = 'whatsapp') {
  return new Promise((resolve, reject) => {
    // The key insight: cmd.exe /c with proper quoting preserves newlines
    // The issue was that spawn with shell:true splits at newlines
    // Solution: pass as environment variable instead of argument
    const env = { ...process.env, MRNA_WA_MSG: message };
    
    // Use PowerShell to read from env var (preserves newlines)
    const ps = spawn('powershell', [
      '-NoProfile', '-Command',
      `& '${path.join(process.env.APPDATA, 'npm', 'openclaw.cmd')}' message send --target '${target}' --message $env:MRNA_WA_MSG --channel '${channel}'`
    ], { env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });

    let out = '', err = '';
    ps.stdout.on('data', d => out += d);
    ps.stderr.on('data', d => err += d);
    ps.on('close', code => {
      if (code === 0) resolve(out.trim());
      else reject(new Error(`Exit ${code}: ${err.trim().substring(0, 200)}`));
    });
    ps.on('error', reject);
    setTimeout(() => { ps.kill(); reject(new Error('Timeout')); }, 20000);
  });
}

const server = http.createServer((req, res) => {
  if (req.method !== 'POST') { res.writeHead(405); res.end(); return; }

  let body = '';
  req.on('data', c => body += c);
  req.on('end', async () => {
    try {
      const { target, message, channel } = JSON.parse(body);
      if (!target || !message) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'target and message required' }));
        return;
      }
      const result = await sendViaCLI(target, message, channel);
      console.log(`OK -> ${target} (${message.length} chars)`);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, output: result }));
    } catch (e) {
      console.error(`FAIL: ${e.message}`);
      res.writeHead(500);
      res.end(JSON.stringify({ error: e.message }));
    }
  });
});

server.listen(PORT, '127.0.0.1', () => console.log(`WA relay v5 on :${PORT}`));
