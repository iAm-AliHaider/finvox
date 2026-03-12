"""Insert blur gate overlay into dashboard."""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "page.tsx"
lines = p.read_text(encoding="utf-8").split("\n")

indent = "          "
overlay = [
    indent + "{/* Security gate: blur until verified */}",
    indent + "{!verified && (",
    indent + '  <div className="absolute inset-0 z-30 backdrop-blur-md bg-white/60 flex items-center justify-center">',
    indent + '    <div className="text-center p-8">',
    indent + '      <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">',
    indent + '        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    indent + "      </div>",
    indent + '      <h3 className="text-lg font-bold text-gray-900 mb-1">Identity Verification Required</h3>',
    indent + '      <p className="text-sm text-gray-500">Please verify your identity using the OTP sent to your WhatsApp</p>',
    indent + "    </div>",
    indent + "  </div>",
    indent + ")}",
]

for i, line in enumerate(lines):
    if 'className="flex"' in line and 'calc(100vh - 60px)' in line:
        lines[i] = lines[i].replace('className="flex"', 'className="flex relative"')
        for j, ol in enumerate(overlay):
            lines.insert(i + 1 + j, ol)
        print(f"Inserted blur gate after line {i+1}")
        break
else:
    print("ERROR: target line not found!")
    raise SystemExit(1)

p.write_text("\n".join(lines), encoding="utf-8")
print("Done")
