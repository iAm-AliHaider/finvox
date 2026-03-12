"""Update MEMORY.md with current MRNA state."""
import pathlib

p = pathlib.Path("C:/Users/AI/.openclaw/workspace/MEMORY.md")
src = p.read_text(encoding="utf-8")

old = """### FinVox -- Voice-First Financial Services Support Agent (2026-03-11)
- **Goal:** Customer support agent for loans + investment/portfolio management company
- **Innovation:** Voice agent + WhatsApp companion (OTP, PDF delivery, post-call summaries)
- **Stack:** LiveKit Agents v1.4 + Deepgram Nova-3 + GPT-4o-mini + Kokoro TTS + Baileys (WA) + Next.js 15 + Neon Postgres
- **Path:** `C:\\Users\\AI\\.openclaw\\workspace\\finvox\\`
- **DB:** Neon Postgres, `finvox` schema (same endpoint, separate schema like pikAui)
- **Rule:** Opus only for all complexity (Boss directive). No API cost compromise.
- **Status file:** `finvox/STATUS.md`
- **Features:**
  - Caller ID by phone number + WhatsApp OTP verification
  - 25+ voice tools (loans, investments, portfolio, compliance)
  - Natural language to SQL (text_to_sql.py pattern)
  - Live supervisor dashboard (caller profile, portfolio charts, transcript, actions)
  - WhatsApp companion (text support, PDF delivery, post-call summary)
  - Session linking (voice + WA = one session)
  - Employee/internal mode with elevated tools
  - Compliance: audit trail, PII masking, dual confirmation for transactions
  - 18 DB tables with realistic financial seed data"""

new = """### MRNA -- Voice-First Financial Services Support Agent (2026-03-11, v3.1 2026-03-12)
- **Goal:** Customer support agent for loans + investment/portfolio management (Saudi Arabia)
- **Stack:** LiveKit Agents v1.4.3 + Deepgram Nova-3 + GPT-4o-mini + Kokoro TTS + Next.js 15 + Neon Postgres
- **Path:** `C:\\Users\\AI\\.openclaw\\workspace\\finvox\\`
- **Live:** https://finvox-app.vercel.app | GitHub: github.com/iAm-AliHaider/finvox
- **Agent:** `mrna` on LiveKit Cloud (India West), port 8086, admin port 8096
- **DB:** Neon Postgres, `finvox` schema | **WA:** OpenClaw CLI (outbound only)
- **33 voice tools** (4 caller + 7 loan + 10 investment + 7 general + 5 employee + NL2SQL)
- **Features (v3.1):**
  - Pre-generated OTP + WhatsApp delivery before session starts
  - Security gate: dashboard blurred until OTP verified
  - 3-step new customer registration (voice+form hybrid)
  - Live transcript via data channel (PII masked)
  - Post-call summary auto-generated and sent via WA
  - Session linking (voice + WA shared context)
  - Employee/internal mode with elevated tools
  - Professional landing page + clean header with status indicators
  - 18 DB tables, Ali Haider (C099) fully seeded with SAR 1.36M portfolio
- **Key patterns:**
  - Events via direct `publish_data()` BEFORE `session.say()` (say blocks entire call)
  - `asyncio.ensure_future(session.say())` for non-blocking greeting
  - v1.4.3 events: `user_input_transcribed`, `conversation_item_added`, `function_tools_executed`
  - Python patch scripts for file edits (PowerShell mangles quotes)
- **DB constraints (hard-won):** loans.type=personal|auto|home|business|education, funds.risk_rating=1-5, funds.category has sukuk not fixed_income, compliance_flags.status=open|investigating|resolved|dismissed"""

src = src.replace(old, new, 1)
p.write_text(src, encoding="utf-8")
print("Updated MEMORY.md")
