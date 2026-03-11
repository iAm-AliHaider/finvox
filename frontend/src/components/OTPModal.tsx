"use client";
import { useState, useRef, useEffect } from "react";

export default function OTPModal({ 
  visible, 
  phone, 
  onSubmit, 
  onClose 
}: {
  visible: boolean;
  phone: string;
  onSubmit: (code: string) => void;
  onClose: () => void;
}) {
  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (visible) {
      setDigits(["", "", "", "", "", ""]);
      setTimeout(() => inputsRef.current[0]?.focus(), 100);
    }
  }, [visible]);

  if (!visible) return null;

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newDigits = [...digits];
    
    // Handle paste of full code
    if (value.length > 1) {
      const chars = value.slice(0, 6).split("");
      chars.forEach((c, i) => { if (i < 6) newDigits[i] = c; });
      setDigits(newDigits);
      const full = newDigits.join("");
      if (full.length === 6) onSubmit(full);
      return;
    }

    newDigits[index] = value;
    setDigits(newDigits);

    // Auto-advance
    if (value && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }

    // Auto-submit when all 6 filled
    const full = newDigits.join("");
    if (full.length === 6) {
      onSubmit(full);
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const maskedPhone = phone ? `${phone.slice(0, 4)}****${phone.slice(-3)}` : "";

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[100]" onClick={onClose}>
      <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 shadow-2xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h3 className="text-lg font-bold text-gray-900">Verify Your Identity</h3>
          <p className="text-sm text-gray-500 mt-1">
            A 6-digit code was sent to your WhatsApp
          </p>
          {maskedPhone && (
            <p className="text-sm font-mono text-gray-700 mt-1">{maskedPhone}</p>
          )}
        </div>

        {/* OTP Inputs */}
        <div className="flex justify-center gap-2 mb-6">
          {digits.map((d, i) => (
            <input
              key={i}
              ref={el => { inputsRef.current[i] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={i === 0 ? 6 : 1}
              value={d}
              onChange={e => handleChange(i, e.target.value)}
              onKeyDown={e => handleKeyDown(i, e)}
              className="w-11 h-13 text-center text-xl font-bold border-2 border-gray-200 rounded-lg 
                         focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
            />
          ))}
        </div>

        {/* Hint */}
        <p className="text-xs text-gray-400 text-center mb-4">
          You can also read the code to the agent
        </p>

        {/* Close */}
        <button 
          onClick={onClose}
          className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
