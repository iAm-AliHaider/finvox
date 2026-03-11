"use client";

export default function TicketPanel({ data }: any) {
  const tickets = data?.tickets || [];
  const openTickets = tickets.filter((t:any) => t.status !== "resolved" && t.status !== "closed");
  const closedTickets = tickets.filter((t:any) => t.status === "resolved" || t.status === "closed");

  const priorityColors: Record<string,string> = {
    low: "badge-info", medium: "badge-warning", high: "badge-danger", urgent: "badge-danger",
  };
  const statusColors: Record<string,string> = {
    open: "badge-info", in_progress: "badge-warning", resolved: "badge-success",
    closed: "badge-neutral", escalated: "badge-danger",
  };

  return (
    <div className="space-y-4 fade-in">
      <div className="grid grid-cols-4 gap-3">
        <div className="card text-center">
          <div className="text-xs text-gray-500">Total Tickets</div>
          <div className="text-lg font-bold">{tickets.length}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Open</div>
          <div className="text-lg font-bold text-blue-600">{openTickets.length}</div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Urgent/High</div>
          <div className="text-lg font-bold text-red-600">
            {openTickets.filter((t:any) => t.priority === "urgent" || t.priority === "high").length}
          </div>
        </div>
        <div className="card text-center">
          <div className="text-xs text-gray-500">Resolved</div>
          <div className="text-lg font-bold text-green-600">{closedTickets.length}</div>
        </div>
      </div>

      {/* Open tickets */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-3">Open Tickets</h3>
        {openTickets.length === 0 ? (
          <p className="text-sm text-gray-400">No open tickets</p>
        ) : (
          <div className="space-y-2">
            {openTickets.map((t:any) => (
              <div key={t.id} className="p-3 rounded-lg border hover:border-blue-200 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium text-sm">{t.subject}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{t.id} | {t.category} | {t.created_at?.slice(0,10)}</div>
                  </div>
                  <div className="flex gap-1">
                    <span className={`badge ${priorityColors[t.priority] || "badge-neutral"}`}>{t.priority}</span>
                    <span className={`badge ${statusColors[t.status] || "badge-neutral"}`}>{t.status?.replace(/_/g," ")}</span>
                  </div>
                </div>
                {t.description && <div className="text-xs text-gray-500 mt-2">{t.description}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resolved tickets */}
      {closedTickets.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-3">Resolved</h3>
          <div className="space-y-2">
            {closedTickets.map((t:any) => (
              <div key={t.id} className="p-3 rounded-lg border border-green-100 bg-green-50/50">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium text-sm">{t.subject}</div>
                    <div className="text-xs text-gray-500">{t.id} | {t.category}</div>
                  </div>
                  <span className="badge badge-success">{t.status}</span>
                </div>
                {t.resolution && <div className="text-xs text-green-700 mt-1">Resolution: {t.resolution}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
