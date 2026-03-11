"use client";
import { useState } from "react";

export default function LoanPanel({ data }: any) {
  const loans = data?.loans || [];
  const payments = data?.loan_payments || [];
  const applications = data?.loan_applications || [];
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);

  const activeLoans = loans.filter((l:any) => l.status === "active");
  const totalOutstanding = activeLoans.reduce((s:number, l:any) => s + parseFloat(l.outstanding || 0), 0);
  const totalPrincipal = activeLoans.reduce((s:number, l:any) => s + parseFloat(l.principal || 0), 0);
  const totalEmi = activeLoans.reduce((s:number, l:any) => s + parseFloat(l.emi_amount || 0), 0);

  const selectedPayments = selectedLoan
    ? payments.filter((p:any) => p.loan_id === selectedLoan)
    : [];

  return (
    <div className="space-y-4 fade-in">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-3">
        <div className="card text-center">
          <div className="text-xs text-gray-500">Total Principal</div>
          <div className="text-lg font-bold">SAR {totalPrincipal.toLocaleString()}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Outstanding</div>
          <div className="text-lg font-bold text-orange-600">SAR {totalOutstanding.toLocaleString()}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Monthly EMI</div>
          <div className="text-lg font-bold">SAR {totalEmi.toLocaleString()}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Active Loans</div>
          <div className="text-lg font-bold">{activeLoans.length}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Loan cards */}
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-900">Loans</h3>
          {loans.map((l:any) => {
            const progress = ((parseFloat(l.principal) - parseFloat(l.outstanding)) / parseFloat(l.principal)) * 100;
            const isSelected = selectedLoan === l.id;
            const overdue = parseInt(l.overdue_count || 0);
            return (
              <div
                key={l.id}
                onClick={() => setSelectedLoan(isSelected ? null : l.id)}
                className={`card cursor-pointer transition-all ${isSelected ? "ring-2 ring-blue-500" : "hover:border-blue-200"}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-medium">{l.type?.charAt(0).toUpperCase()}{l.type?.slice(1)} Loan</div>
                    <div className="text-xs text-gray-500">{l.id}</div>
                  </div>
                  <div className="flex gap-1">
                    <span className={`badge ${l.status === "active" ? "badge-success" : "badge-neutral"}`}>{l.status}</span>
                    {overdue > 0 && <span className="badge badge-danger">{overdue} overdue</span>}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs mb-2">
                  <div><span className="text-gray-400">Principal</span><br/><span className="font-semibold">SAR {parseFloat(l.principal).toLocaleString()}</span></div>
                  <div><span className="text-gray-400">Outstanding</span><br/><span className="font-semibold">SAR {parseFloat(l.outstanding).toLocaleString()}</span></div>
                  <div><span className="text-gray-400">EMI</span><br/><span className="font-semibold">SAR {parseFloat(l.emi_amount).toLocaleString()}</span></div>
                </div>
                <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full bg-blue-500" style={{ width: `${progress}%` }} />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>{progress.toFixed(0)}% repaid</span>
                  <span>{l.interest_rate}% | {l.tenure_months}mo | Due: {l.maturity_date?.slice(0,10)}</span>
                </div>
                {l.collateral && <div className="text-xs text-gray-400 mt-1">Collateral: {l.collateral}</div>}
              </div>
            );
          })}
        </div>

        {/* Payment history / Applications */}
        <div className="space-y-4">
          {selectedLoan ? (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-3">Payment History - {selectedLoan}</h3>
              {selectedPayments.length === 0 ? (
                <p className="text-sm text-gray-400">No payment records</p>
              ) : (
                <div className="space-y-1">
                  {selectedPayments.map((p:any) => {
                    const statusColors: Record<string, string> = {
                      paid: "badge-success", due: "badge-info", overdue: "badge-danger",
                      partial: "badge-warning", waived: "badge-neutral",
                    };
                    return (
                      <div key={p.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50 text-sm">
                        <div>
                          <span className="font-medium">{p.due_date?.slice(0,10)}</span>
                          {p.paid_date && <span className="text-xs text-gray-400 ml-2">Paid: {p.paid_date?.slice(0,10)}</span>}
                        </div>
                        <div className="flex items-center gap-2">
                          <span>SAR {parseFloat(p.amount_due).toLocaleString()}</span>
                          {parseFloat(p.late_fee || 0) > 0 && (
                            <span className="text-xs text-red-500">+{parseFloat(p.late_fee).toLocaleString()} fee</span>
                          )}
                          <span className={`badge ${statusColors[p.status] || "badge-neutral"}`}>{p.status}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-2">Click a loan to see payment history</h3>
              <p className="text-sm text-gray-400">Select a loan card on the left to view its payment schedule and history.</p>
            </div>
          )}

          {/* Loan Applications */}
          {applications.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-3">Loan Applications</h3>
              <div className="space-y-2">
                {applications.map((a:any) => {
                  const statusColors: Record<string, string> = {
                    pending: "badge-warning", docs_required: "badge-warning",
                    under_review: "badge-info", approved: "badge-success",
                    rejected: "badge-danger", disbursed: "badge-success",
                  };
                  return (
                    <div key={a.id} className="p-3 rounded-lg border">
                      <div className="flex justify-between">
                        <div className="font-medium text-sm">{a.type?.charAt(0).toUpperCase()}{a.type?.slice(1)} - SAR {parseFloat(a.amount_requested).toLocaleString()}</div>
                        <span className={`badge ${statusColors[a.status] || "badge-neutral"}`}>
                          {a.status?.replace(/_/g, " ")}
                        </span>
                      </div>
                      {a.purpose && <div className="text-xs text-gray-500 mt-1">{a.purpose}</div>}
                      {a.notes && <div className="text-xs text-blue-600 mt-1">{a.notes}</div>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
