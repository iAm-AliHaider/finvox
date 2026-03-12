"""Replace header: remove search field, enhance design."""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "page.tsx"
lines = p.read_text(encoding="utf-8").split("\n")

# Find header start and end
h_start = None
h_end = None
for i, line in enumerate(lines):
    if "{/* Header */}" in line:
        h_start = i
    if h_start and "</header>" in line:
        h_end = i
        break

if h_start is None or h_end is None:
    print("ERROR: header not found")
    raise SystemExit(1)

new_header = '''      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-sm">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="white" strokeWidth="0"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23" stroke="white" strokeWidth="2"/><line x1="8" y1="23" x2="16" y2="23" stroke="white" strokeWidth="2"/></svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 tracking-tight">MRNA</h1>
            <p className="text-[11px] text-gray-400 font-medium tracking-wide uppercase">Financial Services</p>
          </div>
        </div>

        {/* Center: Status indicators */}
        <div className="flex items-center gap-4">
          {callActive ? (
            <>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-100 rounded-full">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-semibold text-red-600 uppercase tracking-wide">Live Call</span>
              </div>
              {data?.customer && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-full">
                  <span className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white">{(data.customer.name || "?")[0]}</span>
                  <span className="text-xs font-medium text-blue-700">{data.customer.name}</span>
                </div>
              )}
              {isNewCustomer && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-100 rounded-full">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>
                  <span className="text-xs font-semibold text-amber-700">New Customer</span>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-100 rounded-full">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs font-medium text-green-700">Agent Ready</span>
            </div>
          )}
        </div>

        {/* Right: Voice button */}
        <div className="flex items-center gap-3">
          <VoiceButton
            onCallStart={() => setCallActive(true)}
            onCallEnd={() => { setCallActive(false); setAutoCall(false); }}
            onEvent={handleVoiceEvent}
            customerPhone={phone}
            autoStart={autoCall}
            onAutoStartConsumed={() => setAutoCall(false)}
          />
        </div>
      </header>'''

lines[h_start:h_end+1] = new_header.split("\n")
p.write_text("\n".join(lines), encoding="utf-8")
print(f"Replaced header (lines {h_start+1}-{h_end+1})")
