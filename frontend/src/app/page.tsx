"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import CallerProfile from "@/components/CallerProfile";
import LoanPanel from "@/components/LoanPanel";
import PortfolioPanel from "@/components/PortfolioPanel";
import TranscriptPanel from "@/components/TranscriptPanel";
import TicketPanel from "@/components/TicketPanel";
import CompliancePanel from "@/components/CompliancePanel";
import VoiceButton from "@/components/VoiceButton";
import OverviewPanel from "@/components/OverviewPanel";
import OTPModal from "@/components/OTPModal";
import RegistrationForm, { RegistrationData } from "@/components/RegistrationForm";
import DynamicModal, { DynamicModalData } from "@/components/DynamicModal";
import ContextSender from "@/components/ContextSender";

type Tab = "overview" | "loans" | "portfolio" | "transcript" | "tickets" | "compliance";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [phone, setPhone] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [transcript, setTranscript] = useState<Array<{role:string; text:string; time:string}>>([]);
  const [agentActions, setAgentActions] = useState<string[]>([]);
  const [autoCall, setAutoCall] = useState(false);
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [showOTP, setShowOTP] = useState(false);
  const [verified, setVerified] = useState(false);
  const [regVerified, setRegVerified] = useState(false);
  const [voiceFields, setVoiceFields] = useState<Partial<RegistrationData>>({});
  const [dynamicModals, setDynamicModals] = useState<DynamicModalData[]>([]);
  const [toastMessage, setToastMessage] = useState<string>("");
  const [otpPhone, setOtpPhone] = useState("");
  // Reset verified when phone changes
  const resetAuth = useCallback(() => { setVerified(false); setShowOTP(false); }, []);
  const roomRef = useRef<any>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async (cid?: string) => {
    const id = cid || customerId;
    if (!id) return;
    try {
      const r = await fetch(`/api/data?customer_id=${id}`, { cache: "no-store" });
      if (r.ok) {
        const d = await r.json();
        setData(d);
        if (d.customer) setCustomerId(d.customer.id);
      }
    } catch (e) {
      console.error("Fetch error:", e);
    }
  }, [customerId]);

  const lookupAndCall = async () => {
    if (!phone) return;
    setLoading(true);
    setIsNewCustomer(false);
    try {
      const r = await fetch(`/api/data?phone=${encodeURIComponent(phone)}`);
      if (r.ok) {
        const d = await r.json();
        if (d.customer) {
          // Existing customer â€” show profile, then auto-start call
          setData(d);
          setCustomerId(d.customer.id);
          setAutoCall(true);
        } else {
          // API returned OK but no customer â€” treat as new
          setIsNewCustomer(true);
          setData(null);
          setAutoCall(true);
        }
      } else {
        // Not found â€” new customer, start call for registration
        setIsNewCustomer(true);
        setData(null);
        setAutoCall(true);
      }
    } catch (e) {
      console.error("Lookup error:", e);
      // Even on error, allow call
      setIsNewCustomer(true);
      setAutoCall(true);
    }
    setLoading(false);
  };

  // Poll for updates during active call
  useEffect(() => {
    if (callActive && customerId) {
      pollRef.current = setInterval(() => fetchData(), 5000);
      return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }
  }, [callActive, customerId, fetchData]);

  // Refetch data when new customer gets created mid-call
  useEffect(() => {
    if (callActive && !customerId && phone) {
      // Poll to see if customer was created
      const interval = setInterval(async () => {
        try {
          const r = await fetch(`/api/data?phone=${encodeURIComponent(phone)}`, { cache: "no-store" });
          if (r.ok) {
            const d = await r.json();
            if (d.customer) {
              setData(d);
              setCustomerId(d.customer.id);
              setIsNewCustomer(false);
            }
          }
        } catch {}
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [callActive, customerId, phone]);

  const handleVoiceEvent = (event: any) => {
    if (event.type === "transcript") {
      setTranscript(prev => [...prev, {
        role: event.role,
        text: event.text,
        time: new Date().toLocaleTimeString(),
      }]);
    } else if (event.type === "tool_call") {
      setAgentActions(prev => [...prev, event.tool]);
    } else if (event.type === "otp_sent") {
      setOtpPhone(event.phone || phone);
      setShowOTP(true);
    } else if (event.type === "otp_verified") {
      setShowOTP(false);
      setVerified(true);
    } else if (event.type === "customer_identified") {
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
    } else if (event.type === "navigate") {
      // Agent wants to switch tabs
      const validTabs = ["overview", "loans", "portfolio", "transcript", "tickets", "compliance"];
      if (validTabs.includes(event.tab)) {
        setActiveTab(event.tab as Tab);
      }
    } else if (event.type === "show_modal") {
      // Agent generated a dynamic modal
      if (event.modal) {
        setDynamicModals(prev => [...prev, event.modal as DynamicModalData]);
      }
    } else if (event.type === "close_modal") {
      // Agent wants to close a modal
      if (event.modal_id) {
        setDynamicModals(prev => prev.filter(m => m.id !== event.modal_id));
      } else {
        setDynamicModals(prev => prev.slice(0, -1)); // close last
      }
    } else if (event.type === "toast") {
      // Agent wants to show a brief notification
      setToastMessage(event.message || "");
      setTimeout(() => setToastMessage(""), 5000);
    } else if (event.type === "refresh") {
      // Agent wants to refresh data
      fetchData();
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "loans", label: "Loans" },
    { id: "portfolio", label: "Portfolio" },
    { id: "transcript", label: "Transcript" },
    { id: "tickets", label: "Tickets" },
    { id: "compliance", label: "Compliance" },
  ];

  const loanCount = (data?.loans || []).length;
  const portfolioCount = (data?.portfolios || []).length;
  const openTickets = (data?.tickets || []).filter((t:any) => t.status !== "resolved" && t.status !== "closed").length;
  const complianceCount = (data?.compliance || []).filter((c:any) => c.status !== "resolved").length;

  const handleOTPSubmit = (code: string) => {
    // Send OTP to agent via data channel so it can verify without voice
    const room = roomRef.current;
    if (room && room.localParticipant) {
      const payload = JSON.stringify({ type: "otp_submit", code });
      room.localParticipant.publishData(
        new TextEncoder().encode(payload),
        { topic: "ui_sync", reliable: true }
      );
      console.log("[MRNA] OTP sent via data channel:", code);
    } else {
      console.warn("[MRNA] No room/localParticipant for OTP submit, room=", room);
    }
    setShowOTP(false);
    // Don't set verified here - wait for otp_verified event from agent
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* Header */}
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

        {/* Right: Attach DB + Voice button */}
        <div className="flex items-center gap-3">
          <a href="/admin/attach" style={{fontSize:"0.75rem",fontWeight:600,color:"#2563eb",background:"#eff6ff",border:"1px solid #bfdbfe",borderRadius:8,padding:"0.4rem 0.75rem",textDecoration:"none"}}>+ Attach DB</a>
          <VoiceButton
            onCallStart={() => setCallActive(true)}
            onCallEnd={() => { setCallActive(false); setAutoCall(false); }}
            onEvent={handleVoiceEvent}
            customerPhone={phone}
            autoStart={autoCall}
            onAutoStartConsumed={() => setAutoCall(false)}
            onRoomReady={(room: any) => { roomRef.current = room; }}
          />
        </div>
      </header>

      {!data && !callActive ? (
        <div className="min-h-[calc(100vh-60px)] bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
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
        </div>
      ) : !data && callActive ? (
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
        />
      ) : (
        /* Main dashboard â€” customer data loaded */
        <div className="flex relative" style={{ height: "calc(100vh - 60px)" }}>
          {/* Security gate: blur until verified */}
          {!verified && (
            <div className="absolute inset-0 z-30 backdrop-blur-md bg-white/60 flex items-center justify-center">
              <div className="text-center p-8">
                <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center mx-auto mb-4">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Identity Verification Required</h3>
                <p className="text-sm text-gray-500">Please verify your identity using the OTP sent to your WhatsApp</p>
              </div>
            </div>
          )}
          {/* Left sidebar - Caller Profile */}
          <div className="w-80 border-r bg-white overflow-y-auto p-4 flex-shrink-0">
            <CallerProfile data={data} callActive={callActive} agentActions={agentActions} />
          </div>

          {/* Main content */}
          <div className="flex-1 overflow-y-auto">
            {/* Tabs */}
            <div className="bg-white border-b px-4 flex gap-1 sticky top-0 z-40">
              {tabs.map(tab => {
                let count = 0;
                if (tab.id === "loans") count = loanCount;
                if (tab.id === "tickets") count = openTickets;
                if (tab.id === "compliance") count = complianceCount;
                if (tab.id === "portfolio") count = portfolioCount;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? "border-blue-600 text-blue-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {tab.label}
                    {count > 0 && (
                      <span className={`ml-1.5 text-xs px-1.5 py-0.5 rounded-full ${
                        tab.id === "compliance" && count > 0 ? "bg-red-100 text-red-700" :
                        "bg-gray-100 text-gray-600"
                      }`}>{count}</span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Tab content */}
            <div className="p-4">
              {activeTab === "overview" && <OverviewPanel data={data} />}
              {activeTab === "loans" && <LoanPanel data={data} />}
              {activeTab === "portfolio" && <PortfolioPanel data={data} />}
              {activeTab === "transcript" && <TranscriptPanel transcript={transcript} agentActions={agentActions} />}
              {activeTab === "tickets" && <TicketPanel data={data} />}
              {activeTab === "compliance" && <CompliancePanel data={data} />}
            </div>
          </div>
        </div>
      )}

      {/* OTP Verification Modal */}
      <OTPModal
        visible={showOTP}
        phone={otpPhone}
        onSubmit={handleOTPSubmit}
        onClose={() => setShowOTP(false)}
      />

      {/* Dynamic Modals from Agent */}
      {dynamicModals.map(modal => (
        <DynamicModal
          key={modal.id}
          modal={modal}
          onClose={() => setDynamicModals(prev => prev.filter(m => m.id !== modal.id))}
          onAction={(event, payload) => {
            // Send action back to agent via data channel
            const room = roomRef.current;
            if (room && room.localParticipant) {
              const msg = JSON.stringify({ type: "modal_action", event, payload, modal_id: modal.id });
              room.localParticipant.publishData(
                new TextEncoder().encode(msg),
                { topic: "ui_sync", reliable: true }
              );
            }
            // Close modal after action
            setDynamicModals(prev => prev.filter(m => m.id !== modal.id));
          }}
        />
      ))}

      {/* Toast notifications from Agent */}
      {toastMessage && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[110] animate-slide-up">
          <div className="bg-gray-900 text-white px-6 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            {toastMessage}
          </div>
        </div>
      )}

      {/* Context Sender — tells agent what tab user is on */}
      <ContextSender
        room={roomRef.current}
        activeTab={activeTab}
        customerId={customerId}
        verified={verified}
        callActive={callActive}
      />
    </div>
  );
}


