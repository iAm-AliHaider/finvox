"""Wire RegistrationForm into page.tsx."""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "page.tsx"
src = p.read_text(encoding="utf-8")

# 1. Add import
old_import = 'import OTPModal from "@/components/OTPModal";'
new_import = '''import OTPModal from "@/components/OTPModal";
import RegistrationForm, { RegistrationData } from "@/components/RegistrationForm";'''
src = src.replace(old_import, new_import, 1)

# 2. Add voiceFields state after verified state
old_state = '  const [verified, setVerified] = useState(false);'
new_state = '''  const [verified, setVerified] = useState(false);
  const [regVerified, setRegVerified] = useState(false);
  const [voiceFields, setVoiceFields] = useState<Partial<RegistrationData>>({});'''
src = src.replace(old_state, new_state, 1)

# 3. Add registration_field and registration_otp_sent event handlers
old_event = '''    } else if (event.type === "customer_identified") {
      setCustomerId(event.customer_id);
      fetchData(event.customer_id);
      setIsNewCustomer(false);
    }'''
new_event = '''    } else if (event.type === "customer_identified") {
      setCustomerId(event.customer_id);
      fetchData(event.customer_id);
      setIsNewCustomer(false);
    } else if (event.type === "registration_field") {
      // Agent filled a field via voice
      setVoiceFields(prev => ({ ...prev, [event.field]: event.value }));
    } else if (event.type === "registration_otp_sent") {
      setOtpPhone(event.phone || phone);
      setShowOTP(true);
    } else if (event.type === "registration_otp_verified") {
      setRegVerified(true);
      setShowOTP(false);
    } else if (event.type === "account_created") {
      // New account created - fetch their data
      setCustomerId(event.customer_id);
      fetchData(event.customer_id);
      setIsNewCustomer(false);
      setVerified(true);
    }'''
src = src.replace(old_event, new_event, 1)

# 4. Replace the static "New Customer" view with RegistrationForm
# Find the old new customer block
old_new_cust_start = '      ) : !data && callActive ? (\n        /* New customer'
old_new_cust_end = '''            <p className="text-xs text-gray-400 mt-4">Profile will appear here once the account is created.</p>
          </div>
        </div>'''

# Find indices
start_idx = src.find(old_new_cust_start)
end_idx = src.find(old_new_cust_end)
if start_idx == -1 or end_idx == -1:
    print("ERROR: Could not find new customer block!")
    raise SystemExit(1)

end_idx += len(old_new_cust_end)

replacement = '''      ) : !data && callActive ? (
        /* New customer registration form */
        <RegistrationForm
          phone={phone}
          visible={true}
          otpVerified={regVerified}
          onRequestOTP={() => {}}
          onSubmitRegistration={(formData: RegistrationData) => {
            // Send to agent via data channel
            if (roomRef.current && roomRef.current.localParticipant) {
              const payload = JSON.stringify({ type: "registration_submit", ...formData });
              roomRef.current.localParticipant.publishData(
                new TextEncoder().encode(payload),
                { topic: "ui_sync", reliable: true }
              );
            }
          }}
          voiceFields={voiceFields}
        />'''

src = src[:start_idx] + replacement + src[end_idx:]

p.write_text(src, encoding="utf-8")
print("Patched successfully")
