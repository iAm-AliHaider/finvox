"""Add verified gate: blur dashboard until OTP is verified."""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "page.tsx"
src = p.read_text(encoding="utf-8")

# 1. Add verified state
old1 = '  const [showOTP, setShowOTP] = useState(false);'
new1 = '  const [showOTP, setShowOTP] = useState(false);\n  const [verified, setVerified] = useState(false);'
src = src.replace(old1, new1, 1)

# 2. Reset verified on new phone lookup
old2 = '  const [otpPhone, setOtpPhone] = useState("");'
new2 = '  const [otpPhone, setOtpPhone] = useState("");\n  // Reset verified when phone changes\n  const resetAuth = useCallback(() => { setVerified(false); setShowOTP(false); }, []);'
src = src.replace(old2, new2, 1)

# 3. Set verified=true on OTP submit and on otp_verified event
old3 = '''  const handleOTPSubmit = (code: string) => {
    setShowOTP(false);
    // The agent already listens to voice - the user reading the code is enough
    // But we can also send via data channel for reliability
    // For now, the modal is mainly UX - the agent verifies via voice
  };'''
new3 = '''  const handleOTPSubmit = (code: string) => {
    setShowOTP(false);
    setVerified(true);
  };'''
src = src.replace(old3, new3, 1)

# 4. Also set verified on otp_verified event
old4 = '    } else if (event.type === "otp_verified") {\n      setShowOTP(false);'
new4 = '    } else if (event.type === "otp_verified") {\n      setShowOTP(false);\n      setVerified(true);'
src = src.replace(old4, new4, 1)

# 5. Add blur overlay to main dashboard section
old5 = '''        /* Main dashboard \u2014 customer data loaded */
        <div className="flex" style={{ height: "calc(100vh - 60px)" }}>'''
new5 = '''        /* Main dashboard \u2014 customer data loaded */
        <div className="flex relative" style={{ height: "calc(100vh - 60px)" }}>
          {/* Security gate: blur until verified */}
          {!verified && callActive && (
            <div className="absolute inset-0 z-30 backdrop-blur-md bg-white/60 flex items-center justify-center">
              <div className="text-center p-8">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Identity Verification Required</h3>
                <p className="text-sm text-gray-500">Please verify your identity using the OTP sent to your WhatsApp</p>
              </div>
            </div>
          )}'''
src = src.replace(old5, new5, 1)

p.write_text(src, encoding="utf-8")
print("Patched successfully")
