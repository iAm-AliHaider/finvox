"use client";

export default function CompliancePanel({ data }: any) {
  const compliance = data?.compliance || [];
  const customer = data?.customer;

  const open = compliance.filter((c:any) => c.status !== "resolved" && c.status !== "dismissed");
  const resolved = compliance.filter((c:any) => c.status === "resolved" || c.status === "dismissed");

  const severityColors: Record<string, string> = {
    low: "bg-blue-50 border-blue-200 text-blue-800",
    medium: "bg-yellow-50 border-yellow-200 text-yellow-800",
    high: "bg-orange-50 border-orange-200 text-orange-800",
    critical: "bg-red-50 border-red-200 text-red-800",
  };

  return (
    <div className="space-y-4 fade-in">
      {/* KYC Status */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-3">KYC Status</h3>
        <div className="grid grid-cols-4 gap-3">
          <div>
            <div className="text-xs text-gray-500">Status</div>
            <span className={`badge mt-1 ${
              customer?.kyc_status === "valid" ? "badge-success" :
              customer?.kyc_status === "expired" ? "badge-danger" : "badge-warning"
            }`}>{customer?.kyc_status?.toUpperCase()}</span>
          </div>
          <div>
            <div className="text-xs text-gray-500">Expiry</div>
            <div className="text-sm font-medium mt-1">{customer?.kyc_expiry?.slice(0,10) || "N/A"}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Risk Profile</div>
            <div className="text-sm font-medium mt-1">{customer?.risk_profile}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">WhatsApp Verified</div>
            <div className="text-sm font-medium mt-1">{customer?.wa_verified ? "Yes" : "No"}</div>
          </div>
        </div>
      </div>

      {/* Open flags */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-3">
          Active Compliance Flags
          {open.length > 0 && <span className="ml-2 badge badge-danger">{open.length}</span>}
        </h3>
        {open.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-2">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
            <p className="text-sm text-gray-500">No active compliance issues</p>
          </div>
        ) : (
          <div className="space-y-3">
            {open.map((f:any) => (
              <div key={f.id} className={`p-4 rounded-lg border ${severityColors[f.severity] || "bg-gray-50 border-gray-200"}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-sm">
                      {(f.type || "").replace(/_/g, " ").replace(/\b\w/g, (c:string) => c.toUpperCase())}
                    </div>
                    <div className="text-xs mt-1 opacity-80">{f.details}</div>
                  </div>
                  <div className="flex gap-1">
                    <span className={`badge ${
                      f.severity === "critical" ? "badge-danger" :
                      f.severity === "high" ? "badge-warning" : "badge-info"
                    }`}>{f.severity?.toUpperCase()}</span>
                    <span className="badge badge-neutral">{f.status}</span>
                  </div>
                </div>
                <div className="text-xs opacity-60 mt-2">Flagged: {f.flagged_at?.slice(0,10)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolved */}
      {resolved.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Resolved Flags</h3>
          <div className="space-y-2">
            {resolved.map((f:any) => (
              <div key={f.id} className="p-3 rounded-lg border bg-gray-50 text-sm">
                <div className="flex justify-between">
                  <span>{(f.type || "").replace(/_/g, " ")}</span>
                  <span className="badge badge-success">{f.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
