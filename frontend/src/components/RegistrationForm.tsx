"use client";
import { useState, useEffect } from "react";

interface RegistrationFormProps {
  phone: string;
  visible: boolean;
  otpVerified: boolean;
  onRequestOTP: () => void;
  onSubmitRegistration: (data: RegistrationData) => void;
  voiceFields: Partial<RegistrationData>;
}

export interface RegistrationData {
  full_name: string;
  phone: string;
  email: string;
  national_id: string;
  city: string;
}

const STEPS = ["verify", "details", "confirm"] as const;
type Step = typeof STEPS[number];

export default function RegistrationForm({
  phone,
  visible,
  otpVerified,
  onRequestOTP,
  onSubmitRegistration,
  voiceFields,
}: RegistrationFormProps) {
  const [step, setStep] = useState<Step>("verify");
  const [form, setForm] = useState<RegistrationData>({
    full_name: "",
    phone: phone,
    email: "",
    national_id: "",
    city: "",
  });
  const [submitting, setSubmitting] = useState(false);

  // Update phone when prop changes
  useEffect(() => { setForm(f => ({ ...f, phone })); }, [phone]);

  // Voice-filled fields update form in real-time
  useEffect(() => {
    if (voiceFields) {
      setForm(f => ({
        ...f,
        ...(voiceFields.full_name && { full_name: voiceFields.full_name }),
        ...(voiceFields.email && { email: voiceFields.email }),
        ...(voiceFields.national_id && { national_id: voiceFields.national_id }),
        ...(voiceFields.city && { city: voiceFields.city }),
      }));
    }
  }, [voiceFields]);

  // Auto-advance when OTP verified
  useEffect(() => {
    if (otpVerified && step === "verify") setStep("details");
  }, [otpVerified, step]);

  if (!visible) return null;

  const canSubmit = form.full_name.trim().length >= 2;

  const handleSubmit = () => {
    if (!canSubmit) return;
    setSubmitting(true);
    onSubmitRegistration(form);
  };

  return (
    <div className="flex flex-col items-center justify-center" style={{ minHeight: "calc(100vh - 60px)" }}>
      <div className="w-full max-w-lg mx-auto">
        {/* Progress steps */}
        <div className="flex items-center justify-center gap-0 mb-8">
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                step === s ? "bg-blue-600 text-white" :
                STEPS.indexOf(step) > i ? "bg-green-500 text-white" :
                "bg-gray-200 text-gray-500"
              }`}>
                {STEPS.indexOf(step) > i ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                ) : i + 1}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-16 h-1 mx-1 rounded ${STEPS.indexOf(step) > i ? "bg-green-500" : "bg-gray-200"}`} />
              )}
            </div>
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-8">
          {/* Step 1: Verify Phone */}
          {step === "verify" && (
            <div className="text-center">
              <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72"/>
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">Verify Your Phone</h2>
              <p className="text-gray-500 mb-6">
                We'll send a 6-digit code to <span className="font-mono font-bold text-gray-700">{phone}</span> via WhatsApp
              </p>
              {otpVerified ? (
                <div className="flex items-center justify-center gap-2 text-green-600 font-medium">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                  Phone Verified
                </div>
              ) : (
                <p className="text-sm text-gray-400">
                  The agent will send an OTP to your WhatsApp. You can read it out loud or type it in the popup.
                </p>
              )}
            </div>
          )}

          {/* Step 2: Details */}
          {step === "details" && (
            <div>
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Your Details</h2>
                <p className="text-sm text-gray-500">Fill in your information or tell the agent</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={form.full_name}
                    onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                    placeholder="e.g., Mohammed Al-Rashid"
                    className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={form.phone}
                    readOnly
                    className="w-full px-4 py-2.5 border-2 border-gray-100 rounded-lg text-sm bg-gray-50 text-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    placeholder="name@example.com"
                    className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">National ID / Iqama</label>
                    <input
                      type="text"
                      value={form.national_id}
                      onChange={e => setForm(f => ({ ...f, national_id: e.target.value }))}
                      placeholder="10-digit ID"
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                    <input
                      type="text"
                      value={form.city}
                      onChange={e => setForm(f => ({ ...f, city: e.target.value }))}
                      placeholder="e.g., Riyadh"
                      className="w-full px-4 py-2.5 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setStep("confirm")}
                  disabled={!canSubmit}
                  className={`flex-1 py-2.5 rounded-lg font-medium text-sm transition-colors ${
                    canSubmit
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-gray-200 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  Continue
                </button>
              </div>

              <p className="text-xs text-gray-400 text-center mt-3">
                You can also tell the agent your details by voice
              </p>
            </div>
          )}

          {/* Step 3: Confirm */}
          {step === "confirm" && (
            <div>
              <div className="text-center mb-6">
                <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900">Confirm Your Details</h2>
              </div>

              <div className="bg-gray-50 rounded-xl p-4 space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Name</span>
                  <span className="text-sm font-medium text-gray-900">{form.full_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Phone</span>
                  <span className="text-sm font-mono text-gray-900">{form.phone}</span>
                </div>
                {form.email && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Email</span>
                    <span className="text-sm text-gray-900">{form.email}</span>
                  </div>
                )}
                {form.national_id && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">National ID</span>
                    <span className="text-sm font-mono text-gray-900">{form.national_id}</span>
                  </div>
                )}
                {form.city && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">City</span>
                    <span className="text-sm text-gray-900">{form.city}</span>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep("details")}
                  className="flex-1 py-2.5 rounded-lg font-medium text-sm border-2 border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="flex-1 py-2.5 rounded-lg font-medium text-sm bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {submitting ? "Creating Account..." : "Create Account"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Voice hint */}
        <p className="text-center text-xs text-gray-400 mt-4">
          The agent can also collect your details through the call
        </p>
      </div>
    </div>
  );
}
