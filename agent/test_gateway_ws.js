/**
 * Test: Send WA message via gateway WebSocket (same path as message tool).
 */
const WebSocket = require('ws');

const GW_URL = 'ws://127.0.0.1:18789';
const TARGET = '+966534006682';
const MESSAGE = '*GATEWAY WS TEST*\n\nHello Ali,\n\n- Bullet 1 via WebSocket\n- Bullet 2 via WebSocket\n\n_MRNA Financial Services_';

const ws = new WebSocket(GW_URL);

ws.on('open', () => {
  console.log('Connected to gateway WS');
  
  // Try sending a message action (same as message tool)
  const payload = {
    action: 'send',
    channel: 'whatsapp',
    target: TARGET,
    message: MESSAGE,
  };
  
  ws.send(JSON.stringify(payload));
  console.log('Sent payload:', JSON.stringify(payload).substring(0, 100));
});

ws.on('message', (data) => {
  const msg = data.toString();
  console.log('Response:', msg.substring(0, 300));
  ws.close();
});

ws.on('error', (err) => {
  console.error('WS Error:', err.message);
});

ws.on('close', () => {
  console.log('Disconnected');
  process.exit(0);
});

setTimeout(() => { console.log('Timeout'); process.exit(1); }, 10000);
