"""Replace basic welcome screen with professional customer support dashboard landing."""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "page.tsx"
lines = p.read_text(encoding="utf-8").split("\n")

# Find the empty state block
start = None
end = None
for i, line in enumerate(lines):
    if "!data && !callActive" in line:
        start = i
    if start and "!data && callActive" in line:
        end = i
        break

if start is None or end is None:
    print("ERROR: Could not find empty state block")
    raise SystemExit(1)

# Replace everything from start+1 to end-1
new_welcome = '''        <div className="min-h-[calc(100vh-60px)] bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
          {/* Hero Section */}
          <div className="max-w-6xl mx-auto px-6 pt-12 pb-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              {/* Left: Hero content */}
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium mb-6">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                  AI-Powered Support Agent Online
                </div>
                <h1 className="text-4xl font-extrabold text-gray-900 leading-tight mb-4">
                  Customer Support<br />
                  <span className="text-blue-600">Dashboard</span>
                </h1>
                <p className="text-gray-500 text-lg mb-8 leading-relaxed">
                  Look up any customer by phone number. The AI agent handles verification, account lookup, and real-time support.
                </p>

                {/* Search box */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-4 mb-6">
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">Customer Lookup</label>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                      <input
                        type="text"
                        placeholder="+966 5XX XXX XXXX"
                        value={phone}
                        onChange={e => setPhone(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && lookupAndCall()}
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-xl text-sm focus:outline-none focus:border-blue-500 transition-colors bg-gray-50/50"
                      />
                    </div>
                    <button
                      onClick={lookupAndCall}
                      className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
                    >
                      Look Up
                    </button>
                  </div>
                  {/* Quick access chips */}
                  <div className="flex gap-2 flex-wrap mt-3">
                    {[
                      { phone: "+966551234567", name: "Faisal" },
                      { phone: "+966559876543", name: "Layla" },
                      { phone: "+966541112233", name: "Khalid" },
                      { phone: "+966509998877", name: "Noura" },
                    ].map(c => (
                      <button
                        key={c.phone}
                        onClick={() => { setPhone(c.phone); }}
                        className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-gray-50 hover:bg-blue-50 text-gray-600 hover:text-blue-600 border border-gray-200 hover:border-blue-200 cursor-pointer transition-all"
                      >
                        <span className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-500">{c.name[0]}</span>
                        {c.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right: Feature cards */}
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/>', title: "Voice Agent", desc: "AI handles calls with natural conversation", color: "blue" },
                  { icon: '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>', title: "OTP Verification", desc: "WhatsApp-based identity verification", color: "green" },
                  { icon: '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>', title: "Loan Management", desc: "Applications, payments, prepayments", color: "purple" },
                  { icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>', title: "Portfolio Tracking", desc: "Investments, SIPs, fund performance", color: "amber" },
                  { icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>', title: "Compliance", desc: "KYC status, risk flags, audit trail", color: "red" },
                  { icon: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>', title: "New Registration", desc: "Onboard new customers via voice or form", color: "teal" },
                ].map((f, i) => {
                  const colorMap: Record<string, string> = {
                    blue: "bg-blue-50 text-blue-600 border-blue-100",
                    green: "bg-green-50 text-green-600 border-green-100",
                    purple: "bg-purple-50 text-purple-600 border-purple-100",
                    amber: "bg-amber-50 text-amber-600 border-amber-100",
                    red: "bg-red-50 text-red-600 border-red-100",
                    teal: "bg-teal-50 text-teal-600 border-teal-100",
                  };
                  const iconColorMap: Record<string, string> = {
                    blue: "#2563eb", green: "#16a34a", purple: "#9333ea",
                    amber: "#d97706", red: "#dc2626", teal: "#0d9488",
                  };
                  return (
                    <div key={i} className={`rounded-xl border p-4 transition-all hover:shadow-md hover:-translate-y-0.5 ${colorMap[f.color]}`}>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={iconColorMap[f.color]} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" dangerouslySetInnerHTML={{ __html: f.icon }} />
                      <h3 className="font-semibold text-gray-900 text-sm mt-3 mb-1">{f.title}</h3>
                      <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Stats bar */}
          <div className="max-w-6xl mx-auto px-6 pb-8">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { label: "Active Customers", value: "10", sub: "Premium & Retail" },
                { label: "Avg Response", value: "<2s", sub: "AI-powered" },
                { label: "Verification", value: "WhatsApp", sub: "OTP-based" },
                { label: "Coverage", value: "24/7", sub: "Always available" },
              ].map((s, i) => (
                <div key={i} className="text-center">
                  <div className="text-2xl font-bold text-gray-900">{s.value}</div>
                  <div className="text-sm font-medium text-gray-600 mt-1">{s.label}</div>
                  <div className="text-xs text-gray-400">{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>'''

# Replace lines
new_lines = lines[:start+1] + new_welcome.split("\n") + lines[end:]
p.write_text("\n".join(new_lines), encoding="utf-8")
print(f"Replaced lines {start+2}-{end} with new welcome page")
