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

  const lookupCustomer = async () => {
    if (!phone) return;
    setLoading(true);
    try {
      const r = await fetch(`/api/data?phone=${encodeURIComponent(phone)}`);
      if (r.ok) {
        const d = await r.json();
        setData(d);
        if (d.customer) setCustomerId(d.customer.id);
      } else {
        alert("Customer not found");
      }
    } catch (e) {
      alert("Error looking up customer");
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

  const handleVoiceEvent = (event: any) => {
    if (event.type === "transcript") {
      setTranscript(prev => [...prev, {
        role: event.role,
        text: event.text,
        time: new Date().toLocaleTimeString(),
      }]);
    } else if (event.type === "tool_call") {
      setAgentActions(prev => [...prev, event.tool]);
    } else if (event.type === "customer_identified") {
      setCustomerId(event.customer_id);
      fetchData(event.customer_id);
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

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* Header */}
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">FinVox</h1>
            <p className="text-xs text-gray-500">Financial Services Support</p>
          </div>
        </div>

        {/* Customer lookup */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Phone (+966...)"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            onKeyDown={e => e.key === "Enter" && lookupCustomer()}
            className="px-3 py-2 border rounded-lg text-sm w-52 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button onClick={lookupCustomer} disabled={loading} className="btn btn-primary text-sm">
            {loading ? "..." : "Lookup"}
          </button>
        </div>

        {/* Call status */}
        <div className="flex items-center gap-3">
          {callActive && (
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 pulse-ring" />
              <span className="text-sm font-medium text-red-600">LIVE</span>
            </div>
          )}
          <VoiceButton
            onCallStart={() => setCallActive(true)}
            onCallEnd={() => setCallActive(false)}
            onEvent={handleVoiceEvent}
            customerPhone={data?.customer?.phone}
          />
        </div>
      </header>

      {!data ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center" style={{ minHeight: "calc(100vh - 60px)" }}>
          <div className="card text-center max-w-md">
            <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
            </div>
            <h2 className="text-xl font-bold mb-2">Welcome to FinVox</h2>
            <p className="text-gray-500 mb-4">Enter a customer phone number to load their profile, or start a voice call.</p>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="+966551234567"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                onKeyDown={e => e.key === "Enter" && lookupCustomer()}
                className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button onClick={lookupCustomer} className="btn btn-primary">Go</button>
            </div>
            <div className="mt-4 flex gap-2 flex-wrap justify-center">
              {["+966551234567","+966559876543","+966541112233","+966509998877"].map(p => (
                <button key={p} onClick={() => { setPhone(p); }} className="text-xs px-3 py-1 rounded-full bg-gray-100 hover:bg-blue-100 text-gray-600 cursor-pointer transition-colors">
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Main dashboard */
        <div className="flex" style={{ height: "calc(100vh - 60px)" }}>
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
    </div>
  );
}
