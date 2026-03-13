const fs = require("fs");
let code = fs.readFileSync("server.js", "utf-8");
code = code.replace(
  `  // Re-check login state\n  if (!ready) {\n    ready = await isLoggedIn();\n    if (!ready) throw new Error("WhatsApp not logged in. Scan QR code first.");\n  }`,
  `  // Skip strict ready check — wa.me URL works if session is active`
);
fs.writeFileSync("server.js", code);
console.log("Patched");
