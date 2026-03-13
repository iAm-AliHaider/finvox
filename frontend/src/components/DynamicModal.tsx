"use client";
import { useState, useEffect } from "react";

/* ---------- Types ---------- */
export interface ModalColumn {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
  format?: "currency" | "percent" | "date" | "status";
}

export interface ModalKV {
  label: string;
  value: string;
}

export interface ModalChart {
  type: "bar" | "pie" | "progress";
  data: Array<{ label: string; value: number; color?: string }>;
}

export interface ModalAction {
  label: string;
  type: "primary" | "secondary" | "danger";
  event: string;     // data channel event to fire
  payload?: any;
}

export interface DynamicModalData {
  id: string;
  title: string;
  subtitle?: string;
  icon?: string;
  color?: string;     // blue, green, red, purple, amber, teal
  size?: "sm" | "md" | "lg" | "xl";
  sections: ModalSection[];
  actions?: ModalAction[];
  dismissable?: boolean;
}

export type ModalSection =
  | { type: "kv"; items: ModalKV[] }
  | { type: "table"; columns: ModalColumn[]; rows: Record<string, any>[] }
  | { type: "chart"; chart: ModalChart }
  | { type: "text"; content: string }
  | { type: "alert"; level: "info" | "warning" | "error" | "success"; message: string }
  | { type: "list"; items: string[]; ordered?: boolean }
  | { type: "divider" }
  | { type: "summary_box"; items: ModalKV[] };

/* ---------- Helpers ---------- */
const colorMap: Record<string, { bg: string; border: string; text: string; accent: string }> = {
  blue:   { bg: "bg-blue-50",   border: "border-blue-200",   text: "text-blue-700",   accent: "bg-blue-600" },
  green:  { bg: "bg-green-50",  border: "border-green-200",  text: "text-green-700",  accent: "bg-green-600" },
  red:    { bg: "bg-red-50",    border: "border-red-200",    text: "text-red-700",    accent: "bg-red-600" },
  purple: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700", accent: "bg-purple-600" },
  amber:  { bg: "bg-amber-50",  border: "border-amber-200",  text: "text-amber-700",  accent: "bg-amber-600" },
  teal:   { bg: "bg-teal-50",   border: "border-teal-200",   text: "text-teal-700",   accent: "bg-teal-600" },
};

function formatCell(value: any, format?: string): string {
  if (value == null) return "-";
  const s = String(value);
  if (format === "currency") {
    const n = parseFloat(s);
    return isNaN(n) ? s : `SAR ${n.toLocaleString("en-SA", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  }
  if (format === "percent") return `${s}%`;
  if (format === "date") return s.slice(0, 10);
  return s;
}

function statusColor(val: string): string {
  const v = (val || "").toLowerCase();
  if (["active", "paid", "resolved", "success", "completed"].includes(v)) return "bg-green-100 text-green-700";
  if (["overdue", "defaulted", "urgent", "error", "failed"].includes(v)) return "bg-red-100 text-red-700";
  if (["pending", "due", "investigating", "warning"].includes(v)) return "bg-amber-100 text-amber-700";
  if (["closed", "dismissed", "inactive"].includes(v)) return "bg-gray-100 text-gray-500";
  return "bg-blue-100 text-blue-700";
}

const sizeMap: Record<string, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

/* ---------- Components ---------- */
function KVSection({ items }: { items: ModalKV[] }) {
  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-2">
      {items.map((kv, i) => (
        <div key={i} className="flex justify-between py-1.5 border-b border-gray-50">
          <span className="text-xs text-gray-500">{kv.label}</span>
          <span className="text-xs font-semibold text-gray-800">{kv.value}</span>
        </div>
      ))}
    </div>
  );
}

function SummaryBox({ items }: { items: ModalKV[] }) {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
      {items.map((kv, i) => (
        <div key={i} className="flex justify-between py-1.5">
          <span className="text-sm text-gray-600">{kv.label}</span>
          <span className="text-sm font-bold text-blue-700">{kv.value}</span>
        </div>
      ))}
    </div>
  );
}

function TableSection({ columns, rows }: { columns: ModalColumn[]; rows: Record<string, any>[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-100">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-gray-50">
            {columns.map(col => (
              <th key={col.key} className={`px-3 py-2 font-semibold text-gray-600 text-${col.align || "left"}`}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-gray-50 hover:bg-blue-50/30 transition-colors">
              {columns.map(col => {
                const val = row[col.key];
                const formatted = formatCell(val, col.format);
                return (
                  <td key={col.key} className={`px-3 py-2 text-${col.align || "left"}`}>
                    {col.format === "status" ? (
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusColor(String(val))}`}>
                        {String(val || "").charAt(0).toUpperCase() + String(val || "").slice(1)}
                      </span>
                    ) : (
                      <span className="text-gray-700">{formatted}</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartSection({ chart }: { chart: ModalChart }) {
  const max = Math.max(...chart.data.map(d => d.value), 1);
  const defaultColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

  if (chart.type === "bar") {
    return (
      <div className="space-y-2">
        {chart.data.map((d, i) => (
          <div key={i}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-600">{d.label}</span>
              <span className="font-semibold text-gray-800">{d.value.toLocaleString()}</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${(d.value / max) * 100}%`, backgroundColor: d.color || defaultColors[i % 6] }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (chart.type === "progress") {
    return (
      <div className="space-y-3">
        {chart.data.map((d, i) => (
          <div key={i}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-600">{d.label}</span>
              <span className="font-semibold text-gray-800">{d.value}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(d.value, 100)}%`, backgroundColor: d.color || defaultColors[i % 6] }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Pie (simple donut)
  if (chart.type === "pie") {
    const total = chart.data.reduce((s, d) => s + d.value, 0);
    let cumPercent = 0;
    const segments = chart.data.map((d, i) => {
      const pct = (d.value / total) * 100;
      const seg = { ...d, pct, offset: cumPercent, color: d.color || defaultColors[i % 6] };
      cumPercent += pct;
      return seg;
    });

    return (
      <div className="flex items-center gap-6">
        <svg viewBox="0 0 36 36" className="w-24 h-24 flex-shrink-0">
          {segments.map((seg, i) => (
            <circle
              key={i}
              cx="18" cy="18" r="15.9"
              fill="none"
              stroke={seg.color}
              strokeWidth="3.5"
              strokeDasharray={`${seg.pct} ${100 - seg.pct}`}
              strokeDashoffset={`${-seg.offset}`}
              className="transition-all duration-500"
            />
          ))}
        </svg>
        <div className="space-y-1">
          {segments.map((seg, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: seg.color }} />
              <span className="text-gray-600">{seg.label}</span>
              <span className="font-semibold text-gray-800 ml-auto">{seg.pct.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
}

function AlertSection({ level, message }: { level: string; message: string }) {
  const styles: Record<string, string> = {
    info: "bg-blue-50 border-blue-200 text-blue-700",
    warning: "bg-amber-50 border-amber-200 text-amber-700",
    error: "bg-red-50 border-red-200 text-red-700",
    success: "bg-green-50 border-green-200 text-green-700",
  };
  return (
    <div className={`px-4 py-3 rounded-lg border text-xs font-medium ${styles[level] || styles.info}`}>
      {message}
    </div>
  );
}

/* ---------- Main Modal ---------- */
export default function DynamicModal({
  modal,
  onClose,
  onAction,
}: {
  modal: DynamicModalData;
  onClose: () => void;
  onAction?: (event: string, payload?: any) => void;
}) {
  const c = colorMap[modal.color || "blue"];
  const size = sizeMap[modal.size || "md"];

  // Animate in
  const [show, setShow] = useState(false);
  useEffect(() => { requestAnimationFrame(() => setShow(true)); }, []);

  const handleClose = () => {
    setShow(false);
    setTimeout(onClose, 200);
  };

  return (
    <div
      className={`fixed inset-0 z-[100] flex items-center justify-center transition-all duration-200 ${show ? "bg-black/30 backdrop-blur-sm" : "bg-transparent"}`}
      onClick={modal.dismissable !== false ? handleClose : undefined}
    >
      <div
        className={`${size} w-full mx-4 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden transition-all duration-200 ${show ? "scale-100 opacity-100" : "scale-95 opacity-0"}`}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`px-6 py-4 ${c.bg} border-b ${c.border} flex items-center justify-between`}>
          <div>
            <h2 className="text-base font-bold text-gray-900">{modal.title}</h2>
            {modal.subtitle && <p className="text-xs text-gray-500 mt-0.5">{modal.subtitle}</p>}
          </div>
          {modal.dismissable !== false && (
            <button onClick={handleClose} className="w-8 h-8 rounded-lg hover:bg-white/60 flex items-center justify-center transition-colors">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          )}
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
          {modal.sections.map((section, i) => {
            switch (section.type) {
              case "kv": return <KVSection key={i} items={section.items} />;
              case "summary_box": return <SummaryBox key={i} items={section.items} />;
              case "table": return <TableSection key={i} columns={section.columns} rows={section.rows} />;
              case "chart": return <ChartSection key={i} chart={section.chart} />;
              case "text": return <p key={i} className="text-sm text-gray-600 leading-relaxed">{section.content}</p>;
              case "alert": return <AlertSection key={i} level={section.level} message={section.message} />;
              case "list": return (
                <div key={i}>
                  {section.ordered ? (
                    <ol className="list-decimal list-inside space-y-1 text-xs text-gray-600">
                      {section.items.map((item, j) => <li key={j}>{item}</li>)}
                    </ol>
                  ) : (
                    <ul className="space-y-1 text-xs text-gray-600">
                      {section.items.map((item, j) => (
                        <li key={j} className="flex items-start gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-1.5 flex-shrink-0" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
              case "divider": return <hr key={i} className="border-gray-100" />;
              default: return null;
            }
          })}
        </div>

        {/* Actions */}
        {modal.actions && modal.actions.length > 0 && (
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex justify-end gap-2">
            {modal.actions.map((action, i) => {
              const btnStyle = action.type === "primary"
                ? `${c.accent} text-white hover:opacity-90`
                : action.type === "danger"
                ? "bg-red-600 text-white hover:bg-red-700"
                : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50";
              return (
                <button
                  key={i}
                  onClick={() => onAction?.(action.event, action.payload)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${btnStyle}`}
                >
                  {action.label}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
