"use client";
import { useState } from "react";

export default function PortfolioPanel({ data }: any) {
  const portfolios = data?.portfolios || [];
  const holdings = data?.holdings || [];
  const sips = data?.sips || [];
  const transactions = data?.transactions || [];
  const dividends = data?.dividends || [];
  const [selectedPortfolio, setSelectedPortfolio] = useState<string | null>(null);
  const [subTab, setSubTab] = useState<"holdings"|"sips"|"transactions"|"dividends">("holdings");

  const totalInvested = portfolios.reduce((s:number, p:any) => s + parseFloat(p.total_invested || 0), 0);
  const totalValue = portfolios.reduce((s:number, p:any) => s + parseFloat(p.current_value || 0), 0);
  const totalReturns = totalValue - totalInvested;
  const returnsPct = totalInvested > 0 ? ((totalReturns / totalInvested) * 100).toFixed(1) : "0.0";

  // Asset allocation from holdings
  const allocationMap: Record<string, number> = {};
  holdings.forEach((h:any) => {
    const cat = h.category || "other";
    allocationMap[cat] = (allocationMap[cat] || 0) + parseFloat(h.current_value || 0);
  });
  const allocationData = Object.entries(allocationMap).sort((a,b) => b[1] - a[1]);
  const catColors: Record<string, string> = {
    equity: "#2563eb", debt: "#16a34a", hybrid: "#8b5cf6",
    money_market: "#64748b", real_estate: "#ea580c", commodity: "#eab308", sukuk: "#0d9488",
  };

  const filteredHoldings = selectedPortfolio ? holdings.filter((h:any) => h.portfolio_id === selectedPortfolio) : holdings;
  const filteredSips = selectedPortfolio ? sips.filter((s:any) => s.portfolio_id === selectedPortfolio) : sips;
  const filteredTxns = selectedPortfolio ? transactions.filter((t:any) => t.portfolio_id === selectedPortfolio) : transactions;
  const filteredDivs = selectedPortfolio ? dividends.filter((d:any) => d.portfolio_id === selectedPortfolio) : dividends;

  return (
    <div className="space-y-4 fade-in">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-3">
        <div className="card text-center">
          <div className="text-xs text-gray-500">Total Invested</div>
          <div className="text-lg font-bold">SAR {totalInvested.toLocaleString()}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Current Value</div>
          <div className="text-lg font-bold text-blue-600">SAR {totalValue.toLocaleString()}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Total Returns</div>
          <div className={`text-lg font-bold ${totalReturns >= 0 ? "text-green-600" : "text-red-600"}`}>
            {totalReturns >= 0 ? "+" : ""}SAR {totalReturns.toLocaleString()}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Return %</div>
          <div className={`text-lg font-bold ${parseFloat(returnsPct) >= 0 ? "text-green-600" : "text-red-600"}`}>
            {parseFloat(returnsPct) >= 0 ? "+" : ""}{returnsPct}%
          </div>
        </div>
      </div>

      {/* Allocation bar */}
      {allocationData.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Asset Allocation</h3>
          <div className="h-6 rounded-full overflow-hidden flex">
            {allocationData.map(([cat, val]) => {
              const pct = (val / totalValue) * 100;
              return (
                <div
                  key={cat}
                  style={{ width: `${pct}%`, background: catColors[cat] || "#94a3b8" }}
                  className="h-full transition-all"
                  title={`${cat}: ${pct.toFixed(1)}%`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            {allocationData.map(([cat, val]) => (
              <div key={cat} className="flex items-center gap-1.5 text-xs">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: catColors[cat] || "#94a3b8" }} />
                <span className="text-gray-600">{cat.charAt(0).toUpperCase() + cat.slice(1)}: SAR {val.toLocaleString()} ({((val/totalValue)*100).toFixed(1)}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {/* Portfolio cards */}
        <div className="space-y-2">
          <h3 className="font-semibold text-gray-900">Portfolios</h3>
          <button
            onClick={() => setSelectedPortfolio(null)}
            className={`w-full text-left p-3 rounded-lg border text-sm transition-all ${!selectedPortfolio ? "ring-2 ring-blue-500 bg-blue-50" : "hover:border-blue-200"}`}
          >
            All Portfolios
          </button>
          {portfolios.map((p:any) => {
            const ret = parseFloat(p.returns_pct || 0);
            return (
              <div
                key={p.id}
                onClick={() => setSelectedPortfolio(p.id)}
                className={`card cursor-pointer transition-all ${selectedPortfolio === p.id ? "ring-2 ring-blue-500" : "hover:border-blue-200"}`}
              >
                <div className="font-medium text-sm">{p.name}</div>
                <div className="text-xs text-gray-500">{p.type} | Risk: {p.risk_score}/10</div>
                <div className="flex justify-between items-end mt-2">
                  <div className="text-sm font-semibold">SAR {parseFloat(p.current_value).toLocaleString()}</div>
                  <div className={`text-xs font-semibold ${ret >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {ret >= 0 ? "+" : ""}{ret}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Detail panel */}
        <div className="col-span-2 space-y-3">
          {/* Sub tabs */}
          <div className="flex gap-1 border-b">
            {(["holdings","sips","transactions","dividends"] as const).map(t => (
              <button key={t} onClick={() => setSubTab(t)}
                className={`px-3 py-2 text-sm font-medium border-b-2 ${subTab === t ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500"}`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
                {t === "holdings" && <span className="ml-1 text-xs text-gray-400">({filteredHoldings.length})</span>}
              </button>
            ))}
          </div>

          {subTab === "holdings" && (
            <div className="space-y-2">
              {filteredHoldings.map((h:any) => {
                const pnl = parseFloat(h.unrealized_pnl || 0);
                return (
                  <div key={h.id} className="card p-3">
                    <div className="flex justify-between">
                      <div>
                        <div className="text-sm font-medium">{h.fund_name}</div>
                        <div className="text-xs text-gray-500">
                          {h.category} | Risk: {h.risk_rating}/5 | 1Y: {h.return_1y}%
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold">SAR {parseFloat(h.current_value || 0).toLocaleString()}</div>
                        <div className={`text-xs ${pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {pnl >= 0 ? "+" : ""}SAR {pnl.toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {parseFloat(h.units).toLocaleString()} units @ SAR {parseFloat(h.avg_buy_price).toFixed(2)} avg | NAV: SAR {parseFloat(h.latest_nav || 0).toFixed(2)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {subTab === "sips" && (
            <div className="space-y-2">
              {filteredSips.length === 0 ? <p className="text-sm text-gray-400">No SIPs</p> : filteredSips.map((s:any) => (
                <div key={s.id} className="card p-3">
                  <div className="flex justify-between">
                    <div>
                      <div className="text-sm font-medium">{s.fund_name}</div>
                      <div className="text-xs text-gray-500">SAR {parseFloat(s.amount).toLocaleString()}/{s.frequency} on day {s.day_of_month}</div>
                    </div>
                    <div className="text-right">
                      <span className={`badge ${s.status === "active" ? "badge-success" : s.status === "paused" ? "badge-warning" : "badge-neutral"}`}>{s.status}</span>
                      <div className="text-xs text-gray-400 mt-1">Next: {s.next_date?.slice(0,10)}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {s.installments_done} installments | Total: SAR {parseFloat(s.total_invested || 0).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}

          {subTab === "transactions" && (
            <div className="space-y-1">
              {filteredTxns.length === 0 ? <p className="text-sm text-gray-400">No transactions</p> : filteredTxns.map((t:any) => {
                const typeColors: Record<string,string> = {
                  buy: "text-green-600", sell: "text-red-600", sip: "text-blue-600",
                  switch_in: "text-purple-600", switch_out: "text-orange-600", dividend_reinvest: "text-teal-600",
                };
                return (
                  <div key={t.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50 text-sm">
                    <div>
                      <span className={`font-semibold ${typeColors[t.type] || ""}`}>{t.type?.toUpperCase()}</span>
                      <span className="ml-2 text-gray-600">{t.fund_name}</span>
                    </div>
                    <div className="text-right">
                      <span className="font-medium">SAR {parseFloat(t.amount).toLocaleString()}</span>
                      <span className="text-xs text-gray-400 ml-2">{t.executed_at?.slice(0,10)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {subTab === "dividends" && (
            <div className="space-y-1">
              {filteredDivs.length === 0 ? <p className="text-sm text-gray-400">No dividends</p> : filteredDivs.map((d:any) => (
                <div key={d.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50 text-sm">
                  <div>
                    <span className="font-medium">{d.fund_name}</span>
                    <span className={`ml-2 text-xs ${d.reinvested ? "text-blue-500" : "text-green-500"}`}>
                      {d.reinvested ? "Reinvested" : "Paid out"}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-medium">SAR {parseFloat(d.amount).toLocaleString()}</span>
                    <span className="text-xs text-gray-400 ml-2">{d.record_date?.slice(0,10)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
