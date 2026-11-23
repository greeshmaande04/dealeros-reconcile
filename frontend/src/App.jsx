import { useEffect, useState } from "react";

const REASONS = ["", "MISSING_IN_B", "ORPHAN_IN_B", "DUPLICATE_IN_B", "VALUE_MISMATCH",
  "LOCATION_MISMATCH", "DATE_MISMATCH", "VOIDED_IN_B"];

export default function App() {
  const [org, setOrg] = useState("ORG-A");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("");
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const q = new URLSearchParams({ org, ...(reason && { reason }), ...(sort && { sort }) });
    fetch(`${import.meta.env.VITE_API_URL || ""}/api/disagreements/?${q}`)
      .then((r) => r.json())
      .then((d) => { setRows(d.results || []); setError(d.error || ""); })
      .catch(() => setError("Could not reach the API"));
  }, [org, reason, sort]);

  const diff = (r) =>
    r.a_value !== null && r.b_value !== null ? (Number(r.a_value) - Number(r.b_value)).toFixed(2) : "";
  const toggleSort = () => setSort(sort === "value" ? "-value" : "value");

  return (
    <div style={{ padding: 16, fontFamily: "sans-serif" }}>
      <h2>DealerOS disagreements</h2>
      <select value={org} onChange={(e) => setOrg(e.target.value)}>
        <option>ORG-A</option><option>ORG-B</option>
      </select>{" "}
      <select value={reason} onChange={(e) => setReason(e.target.value)}>
        {REASONS.map((r) => <option key={r} value={r}>{r || "All reasons"}</option>)}
      </select>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {!error && rows.length === 0 && <p>No disagreements found.</p>}
      {rows.length > 0 && (
        <table border="1" cellPadding="6" style={{ marginTop: 12, borderCollapse: "collapse" }}>
          <thead><tr>
            <th>Reason</th><th>Record ID</th><th>Location (A / B)</th>
            <th onClick={toggleSort} style={{ cursor: "pointer" }}>
              A value {sort === "value" ? "▲" : sort === "-value" ? "▼" : ""}</th>
            <th>B value</th><th>Difference</th>
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r.reason}</td><td>{r.record_id}</td>
                <td>{r.a_location ?? ""} / {r.b_location ?? ""}</td>
                <td>{r.a_value ?? ""}</td><td>{r.b_value ?? ""}</td><td>{diff(r)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}