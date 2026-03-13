const WebSocket = require('ws');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const cfg = JSON.parse(fs.readFileSync(path.join(process.env.USERPROFILE, '.openclaw', 'openclaw.json'), 'utf-8'));
const TOKEN = cfg?.gateway?.auth?.token || '';
console.log('Token len:', TOKEN.length);

const ws = new WebSocket('ws://127.0.0.1:18789');

ws.on('open', () => console.log('WS open'));
ws.on('error', e => console.error('WS error:', e.message));
ws.on('close', (code, reason) => console.log('WS close:', code, reason.toString()));

ws.on('message', (data) => {
  const raw = data.toString();
  console.log('<<', raw.substring(0, 500));
  
  try {
    const msg = JSON.parse(raw);
    
    if (msg.event === 'connect.challenge') {
      const nonce = msg.payload.nonce;
      console.log('Got challenge, nonce:', nonce);
      
      // Try HMAC
      const hmac = crypto.createHmac('sha256', TOKEN).update(nonce).digest('hex');
      
      // Try different auth formats
      const authPayload = {
        type: 'request',
        method: 'connect',
        id: '1',
        params: {
          response: hmac,
          protocol: 16,
          token: TOKEN,  // maybe it wants the raw token?
        },
      };
      console.log('>>', JSON.stringify(authPayload).substring(0, 200));
      ws.send(JSON.stringify(authPayload));
    } else {
      console.log('Other msg type:', msg.type, msg.method, msg.event);
    }
  } catch (e) {
    console.log('Parse error:', e.message);
  }
});

setTimeout(() => { console.log('Done'); ws.close(); process.exit(0); }, 8000);
