"use client";

export default function OverviewPanel({ data }: any) {
  const customer = data?.customer;
  const loans = data?.loans || [];
  const portfolios = data?.portfolios || [];
  const tickets = data?.tickets || [];
  const interactions = data?.interactions || [];
  const compliance = (data?.compliance || []).filter((c:any) => c.status !== "resolved");

  const activeLoans = loans.filter((l:any) => l.status === "active");
  const totalOutstanding = activeLoans.reduce((s:number, l:any) => s + parseFloat(l.outstanding || 0), 0);
  const totalEmi = activeLoans.reduce((s:number, l:any) => s + parseFloat(l.emi_amount || 0), 0);
  const overdueLoans = loans.filter((l:any) => parseInt(l.overdue_count || 0) > 0);

  const totalInvested = portfolios.reduce((s:number, p:any) => s + parseFloat(p.total_invested || 0), 0);
  const totalValue = portfolios.reduce((s:number, p:any) => s + parseFloat(p.current_value || 0), 0);
  const totalReturns = totalValue - totalInvested;
  const returnsPct = totalInvested > 0 ? ((totalReturns / totalInvested) * 100).toFixed(1) : "0.0";

  const openTickets = tickets.filter((t:any) => t.status !== "resolved" && t.status !== "closed");

  return (
    <div className="space-y-4 fade-in">
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <div className="text-xs text-gray-500 font-medium">Total Portfolio Value</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">SAR {totalValue.toLocaleString()}</div>
          <div className={`text-sm mt-1 ${totalReturns >= 0 ? "text-green-600" : "text-red-600"}`}>
            {totalReturns >= 0 ? "+" : ""}SAR {totalReturns.toLocaleString()} ({returnsPct}%)
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 font-medium">Loan Outstanding</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">SAR {totalOutstanding.toLocaleString()}</div>
          <div className="text-sm text-gray-500 mt-1">
            {activeLoans.length} active | EMI: SAR {totalEmi.toLocaleString()}/mo
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 font-medium">Open Tickets</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{openTickets.length}</div>
          <div className="text-sm text-gray-500 mt-1">
            {openTickets.filter((t:any) => t.priority === "urgent" || t.priority === "high").length} high priority
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 font-medium">Compliance</div>
          <div className={`text-2xl font-bold mt-1 ${compliance.length > 0 ? "text-red-600" : "text-green-600"}`}>
            {compliance.length > 0 ? `${compliance.length} Alert${compliance.length > 1 ? "s" : ""}` : "Clear"}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            {compliance.filter((c:any) => c.severity === "critical").length} critical
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Loans overview */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Active Loans</h3>
          {activeLoans.length === 0 ? (
            <p className="text-sm text-gray-400">No active loans</p>
          ) : (
            <div className="space-y-2">
              {activeLoans.map((l:any) => {
                const progress = ((parseFloat(l.principal) - parseFloat(l.outstanding)) / parseFloat(l.principal)) * 100;
                const hasOverdue = parseInt(l.overdue_count || 0) > 0;
                return (
                  <div key={l.id} className="p-3 rounded-lg border hover:border-blue-200 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-medium">{(l.type || "").charAt(0).toUpperCase() + l.type.slice(1)} Loan</div>
                        <div className="text-xs text-gray-500">{l.id} | {l.interest_rate}% | EMI: SAR {parseFloat(l.emi_amount).toLocaleString()}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">SAR {parseFloat(l.outstanding).toLocaleString()}</div>
                        {hasOverdue && <span className="badge badge-danger text-xs">OVERDUE</span>}
                      </div>
                    </div>
                    <div className="mt-2 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                      <div className="h-full rounded-full bg-blue-500 transition-all" style={{ width: `${progress}%` }} />
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{progress.toFixed(0)}% repaid | Maturity: {l.maturity_date?.slice(0,10)}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Portfolio overview */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Portfolios</h3>
          {portfolios.length === 0 ? (
            <p className="text-sm text-gray-400">No investment portfolios</p>
          ) : (
            <div className="space-y-2">
              {portfolios.map((p:any) => {
                const ret = parseFloat(p.returns_pct || 0);
                return (
                  <div key={p.id} className="p-3 rounded-lg border hover:border-blue-200 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-medium">{p.name}</div>
                        <div className="text-xs text-gray-500">{p.type} | Risk: {p.risk_score}/10</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">SAR {parseFloat(p.current_value).toLocaleString()}</div>
                        <div className={`text-xs ${ret >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {ret >= 0 ? "+" : ""}{ret}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent interactions */}
      {interactions.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Recent Interactions</h3>
          <div className="space-y-2">
            {interactions.slice(0, 5).map((int:any) => (
              <div key={int.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  int.channel === "voice" ? "bg-blue-100 text-blue-700" :
                  int.channel === "whatsapp" ? "bg-green-100 text-green-700" :
                  "bg-gray-100 text-gray-700"
                }`}>
                  {int.channel === "voice" ? "V" : int.channel === "whatsapp" ? "W" : "E"}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm">{int.summary || "No summary"}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {int.created_at?.slice(0,10)} | {int.channel} | 
                    {int.duration_seconds ? ` ${Math.floor(int.duration_seconds/60)}m ${int.duration_seconds%60}s` : ""}
                    {int.sentiment && (
                      <span className={`ml-2 ${
                        int.sentiment === "positive" ? "text-green-500" :
                        int.sentiment === "negative" ? "text-red-500" : "text-gray-400"
                      }`}>{int.sentiment}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
