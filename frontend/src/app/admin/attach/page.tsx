"use client";
import { useState } from "react";

interface TableInfo {
  columns: { name: string; type: string; primary_key: boolean }[];
  row_count: number;
  samples: Record<string, unknown>[];
}

interface TestResult {
  success: boolean;
  tables: number;
  table_names: string[];
  total_rows_sample: number;
  error?: string;
}

export default function AttachDatabasePage() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [form, setForm] = useState({
    database_url: "",
    schema: "public",
    business_name: "",
    business_context: "",
    greeting: "",
    currency: "SAR",
    caller_table: "customers",
    caller_id_field: "phone",
    config_name: "",
  });
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activating, setActivating] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  async function testConnection() {
    setTesting(true);
    setError("");
    setTestResult(null);
    try {
      const r = await fetch("/api/admin/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ database_url: form.database_url, schema: form.schema }),
      });
      const d = await r.json();
      setTestResult(d);
      if (d.success) {
        setStep(2);
        // Auto-suggest caller table
        const tables = d.table_names as string[];
        const callerTbl = tables.find(t => /customer|user|client|member|contact/i.test(t)) || tables[0];
        if (callerTbl) set("caller_table", callerTbl);
        if (!form.config_name) set("config_name", "client_" + Date.now());
      }
    } catch (e) {
      setError("Connection failed: " + (e as Error).message);
    } finally {
      setTesting(false);
    }
  }

  async function saveConfig() {
    setSaving(true);
    setError("");
    try {
      const r = await fetch("/api/admin/configs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (!r.ok) { setError(d.error); return; }
      setSaved(true);
      setStep(3);
    } catch (e) {
      setError("Save failed: " + (e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function activateConfig() {
    setActivating(true);
    setError("");
    try {
      const r = await fetch("/api/admin/configs/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.config_name }),
      });
      const d = await r.json();
      if (!r.ok) { setError(d.error); return; }
    } catch (e) {
      setError("Activation failed: " + (e as Error).message);
    } finally {
      setActivating(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "Inter, sans-serif" }}>
      {/* Header */}
      <div style={{ background: "white", borderBottom: "1px solid #e2e8f0", padding: "1rem 2rem", display: "flex", alignItems: "center", gap: "1rem" }}>
        <span style={{ fontSize: "1.5rem", fontWeight: 800, background: "linear-gradient(135deg,#2563eb,#7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>MRNA</span>
        <span style={{ color: "#64748b", fontSize: "0.9rem" }}>/ Attach Client Database</span>
      </div>

      <div style={{ maxWidth: 720, margin: "2rem auto", padding: "0 1rem" }}>
        {/* Steps */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
          {[
            { n: 1, label: "Connect Database" },
            { n: 2, label: "Configure Agent" },
            { n: 3, label: "Activate" },
          ].map(s => (
            <div key={s.n} style={{ display: "flex", alignItems: "center", gap: "0.5rem", opacity: step >= s.n ? 1 : 0.4 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                background: step > s.n ? "#22c55e" : step === s.n ? "#2563eb" : "#e2e8f0",
                color: step >= s.n ? "white" : "#64748b", fontSize: "0.8rem", fontWeight: 700,
              }}>
                {step > s.n ? "✓" : s.n}
              </div>
              <span style={{ fontSize: "0.85rem", fontWeight: step === s.n ? 600 : 400, color: step === s.n ? "#1e293b" : "#64748b" }}>{s.label}</span>
              {s.n < 3 && <span style={{ color: "#e2e8f0", marginLeft: 4 }}>→</span>}
            </div>
          ))}
        </div>

        {/* Step 1: Connect */}
        {step === 1 && (
          <div style={{ background: "white", borderRadius: 12, padding: "1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,.06)" }}>
            <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.1rem", fontWeight: 700 }}>Connect Your Client Database</h2>
            <p style={{ margin: "0 0 1.5rem", color: "#64748b", fontSize: "0.875rem" }}>
              Paste the connection string and the agent will auto-discover the schema.
              Supports PostgreSQL, MySQL, SQLite.
            </p>

            <label style={labelStyle}>Database URL</label>
            <input
              style={{ ...inputStyle, fontFamily: "monospace", fontSize: "0.8rem" }}
              placeholder="postgresql://user:pass@host/database?sslmode=require"
              value={form.database_url}
              onChange={e => set("database_url", e.target.value)}
            />

            <label style={labelStyle}>Schema Name</label>
            <input style={inputStyle} placeholder="public" value={form.schema} onChange={e => set("schema", e.target.value)} />

            {error && <div style={errorStyle}>{error}</div>}

            <button style={{ ...btnStyle, background: "#2563eb" }} onClick={testConnection} disabled={!form.database_url || testing}>
              {testing ? "Testing..." : "Test Connection & Discover Schema"}
            </button>
          </div>
        )}

        {/* Step 2: Configure */}
        {step === 2 && testResult?.success && (
          <div style={{ background: "white", borderRadius: 12, padding: "1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,.06)" }}>
            {/* Schema summary */}
            <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "1rem", marginBottom: "1.5rem" }}>
              <div style={{ fontWeight: 700, color: "#166534", marginBottom: "0.5rem" }}>
                Connected! Found {testResult.tables} tables, ~{testResult.total_rows_sample.toLocaleString()} rows
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {testResult.table_names.map(t => (
                  <span key={t} style={{ background: "#dcfce7", color: "#166534", borderRadius: 4, padding: "2px 8px", fontSize: "0.75rem", fontWeight: 500 }}>{t}</span>
                ))}
              </div>
            </div>

            <h2 style={{ margin: "0 0 1.5rem", fontSize: "1.1rem", fontWeight: 700 }}>Configure Agent</h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={labelStyle}>Business Name *</label>
                <input style={inputStyle} placeholder="Acme Corp" value={form.business_name} onChange={e => set("business_name", e.target.value)} />
              </div>
              <div>
                <label style={labelStyle}>Currency</label>
                <input style={inputStyle} placeholder="SAR" value={form.currency} onChange={e => set("currency", e.target.value)} />
              </div>
            </div>

            <label style={labelStyle}>Business Context (what does this company do?)</label>
            <textarea
              style={{ ...inputStyle, height: 80, resize: "vertical" }}
              placeholder="E.g. Online electronics retailer in Saudi Arabia. Customers call for order status, returns, and product inquiries."
              value={form.business_context}
              onChange={e => set("business_context", e.target.value)}
            />

            <label style={labelStyle}>Welcome Greeting</label>
            <input style={inputStyle} placeholder="Welcome to Acme Support! How can I help you today?" value={form.greeting} onChange={e => set("greeting", e.target.value)} />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
              <div>
                <label style={labelStyle}>Caller Table (which table has your customers?)</label>
                <select style={inputStyle} value={form.caller_table} onChange={e => set("caller_table", e.target.value)}>
                  {testResult.table_names.map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>Phone Field (column used to identify caller)</label>
                <input style={inputStyle} placeholder="phone" value={form.caller_id_field} onChange={e => set("caller_id_field", e.target.value)} />
              </div>
            </div>

            <label style={labelStyle}>Config Name (internal reference)</label>
            <input style={inputStyle} placeholder="acme_corp" value={form.config_name} onChange={e => set("config_name", e.target.value)} />

            {error && <div style={errorStyle}>{error}</div>}

            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button style={{ ...btnStyle, background: "#64748b" }} onClick={() => setStep(1)}>Back</button>
              <button style={{ ...btnStyle, background: "#2563eb", flex: 1 }} onClick={saveConfig} disabled={!form.business_name || !form.config_name || saving}>
                {saving ? "Saving..." : "Save Configuration"}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Activate */}
        {step === 3 && (
          <div style={{ background: "white", borderRadius: 12, padding: "2rem", boxShadow: "0 1px 4px rgba(0,0,0,.06)", textAlign: "center" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🎯</div>
            <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.2rem", fontWeight: 700 }}>Configuration Saved!</h2>
            <p style={{ color: "#64748b", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
              <strong>{form.business_name}</strong> config saved as <code>{form.config_name}</code>.<br />
              Activate it to make the agent use this database.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 320, margin: "0 auto" }}>
              <button style={{ ...btnStyle, background: "#2563eb" }} onClick={activateConfig} disabled={activating}>
                {activating ? "Activating..." : "Activate This Config"}
              </button>
              <button style={{ ...btnStyle, background: "#f1f5f9", color: "#475569" }} onClick={() => { setStep(1); setForm({ database_url: "", schema: "public", business_name: "", business_context: "", greeting: "", currency: "SAR", caller_table: "customers", caller_id_field: "phone", config_name: "" }); setTestResult(null); setSaved(false); }}>
                Attach Another Database
              </button>
              <a href="/" style={{ ...btnStyle, background: "#f1f5f9", color: "#475569", textDecoration: "none", display: "block" }}>
                Back to Dashboard
              </a>
            </div>

            {error && <div style={{ ...errorStyle, maxWidth: 320, margin: "1rem auto 0" }}>{error}</div>}
          </div>
        )}

        {/* Info box */}
        <div style={{ marginTop: "1.5rem", background: "white", borderRadius: 12, padding: "1.25rem", boxShadow: "0 1px 4px rgba(0,0,0,.06)" }}>
          <div style={{ fontWeight: 600, fontSize: "0.875rem", marginBottom: "0.75rem" }}>How it works</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {[
              ["Connect", "Paste your client's DB connection string — we auto-discover all tables"],
              ["Configure", "Tell the agent your business name, context, and which table has customers"],
              ["Activate", "Agent instantly becomes their support agent — no code changes needed"],
              ["Call", "When a customer calls, agent looks up their data in real-time and generates UI"],
            ].map(([title, desc]) => (
              <div key={title} style={{ display: "flex", gap: "0.75rem", fontSize: "0.825rem" }}>
                <div style={{ width: 80, fontWeight: 600, color: "#2563eb", flexShrink: 0 }}>{title}</div>
                <div style={{ color: "#64748b" }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = { display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#374151", marginBottom: "0.4rem", marginTop: "1rem" };
const inputStyle: React.CSSProperties = { width: "100%", padding: "0.6rem 0.75rem", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.875rem", boxSizing: "border-box", outline: "none" };
const btnStyle: React.CSSProperties = { padding: "0.7rem 1.5rem", borderRadius: 8, border: "none", color: "white", fontWeight: 600, cursor: "pointer", fontSize: "0.875rem", width: "100%" };
const errorStyle: React.CSSProperties = { background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "0.75rem", color: "#dc2626", fontSize: "0.8rem", marginTop: "1rem" };
