"use client";

export default function CallerProfile({ data, callActive, agentActions }: any) {
  const customer = data?.customer;
  const rm = data?.rm;
  const loans = data?.loans || [];
  const portfolios = data?.portfolios || [];
  const compliance = (data?.compliance || []).filter((c:any) => c.status !== "resolved");

  if (!customer) return null;

  const totalInvested = portfolios.reduce((s:number, p:any) => s + parseFloat(p.total_invested || 0), 0);
  const totalValue = portfolios.reduce((s:number, p:any) => s + parseFloat(p.current_value || 0), 0);
  const totalOutstanding = loans.filter((l:any) => l.status === "active").reduce((s:number, l:any) => s + parseFloat(l.outstanding || 0), 0);

  const tierColors: Record<string, string> = {
    retail: "bg-gray-100 text-gray-700",
    premium: "bg-blue-100 text-blue-700",
    hnw: "bg-purple-100 text-purple-700",
    uhnw: "bg-amber-100 text-amber-700",
  };

  const kycColors: Record<string, string> = {
    valid: "badge-success",
    expired: "badge-danger",
    pending: "badge-warning",
    rejected: "badge-danger",
  };

  return (
    <div className="space-y-4">
      {/* Call indicator */}
      {callActive && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-red-50 border border-red-200 fade-in">
          <span className="w-2 h-2 rounded-full bg-red-500 pulse-ring" />
          <span className="text-xs font-semibold text-red-700">LIVE CALL</span>
        </div>
      )}

      {/* Name & tier */}
      <div>
        <h2 className="text-lg font-bold text-gray-900">{customer.name}</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className={`badge ${tierColors[customer.tier] || "bg-gray-100"}`}>
            {(customer.tier || "").toUpperCase()}
          </span>
          <span className={`badge ${kycColors[customer.kyc_status] || "badge-neutral"}`}>
            KYC: {customer.kyc_status}
          </span>
        </div>
      </div>

      {/* Contact */}
      <div className="text-sm space-y-1">
        <div className="flex items-center gap-2 text-gray-600">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72"/></svg>
          {customer.phone}
        </div>
        {customer.email && (
          <div className="flex items-center gap-2 text-gray-600">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            {customer.email}
          </div>
        )}
        <div className="flex items-center gap-2 text-gray-600">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
          {customer.city}, {customer.country}
        </div>
        <div className="text-gray-400 text-xs">
          ID: {customer.id} | Risk: {customer.risk_profile} | Since: {customer.onboarded_at?.slice(0,10)}
        </div>
      </div>

      {/* RM */}
      {rm && (
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
          <div className="text-xs font-semibold text-blue-600 mb-1">RELATIONSHIP MANAGER</div>
          <div className="text-sm font-medium">{rm.name}</div>
          <div className="text-xs text-gray-500">{rm.department} | {rm.phone}</div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 rounded-lg bg-green-50 border border-green-100 text-center">
          <div className="text-xs text-gray-500">Portfolio Value</div>
          <div className="text-sm font-bold text-green-700">SAR {(totalValue/1000).toFixed(0)}K</div>
        </div>
        <div className="p-3 rounded-lg bg-orange-50 border border-orange-100 text-center">
          <div className="text-xs text-gray-500">Loan Outstanding</div>
          <div className="text-sm font-bold text-orange-700">SAR {(totalOutstanding/1000).toFixed(0)}K</div>
        </div>
      </div>

      {/* Compliance alerts */}
      {compliance.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-red-600">ALERTS ({compliance.length})</div>
          {compliance.map((c:any, i:number) => (
            <div key={i} className="p-2 rounded-lg bg-red-50 border border-red-100 text-xs">
              <span className="font-semibold text-red-700">[{(c.severity||"").toUpperCase()}]</span>{" "}
              {(c.type||"").replace(/_/g, " ")}
              <div className="text-gray-500 mt-0.5">{(c.details||"").slice(0,80)}</div>
            </div>
          ))}
        </div>
      )}

      {/* Agent actions log */}
      {agentActions.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs font-semibold text-gray-500">AGENT ACTIONS</div>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {agentActions.map((action:string, i:number) => (
              <div key={i} className="text-xs px-2 py-1 rounded bg-gray-50 text-gray-600 font-mono fade-in">
                {action}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
