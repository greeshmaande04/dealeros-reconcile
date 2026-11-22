from django.http import HttpResponse

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>DealerOS disagreements</title></head>
<body style="font-family:sans-serif;padding:16px">
<h2>DealerOS disagreements</h2>
<select id="org"><option>ORG-A</option><option>ORG-B</option></select>
<select id="reason">
<option value="">All reasons</option><option>MISSING_IN_B</option><option>ORPHAN_IN_B</option>
<option>DUPLICATE_IN_B</option><option>VALUE_MISMATCH</option><option>LOCATION_MISMATCH</option>
<option>DATE_MISMATCH</option><option>VOIDED_IN_B</option></select>
<p id="msg"></p>
<table border="1" cellpadding="6" style="border-collapse:collapse"><thead><tr>
<th>Reason</th><th>Record ID</th><th>Location (A / B)</th>
<th id="sortcol" style="cursor:pointer">A value (click to sort)</th><th>B value</th><th>Difference</th>
</tr></thead><tbody id="rows"></tbody></table>
<script>
let sort = "";
const $ = (id) => document.getElementById(id);
async function load() {
  const q = new URLSearchParams({org: $("org").value});
  if ($("reason").value) q.set("reason", $("reason").value);
  if (sort) q.set("sort", sort);
  const res = await fetch("/api/disagreements/?" + q);
  const data = await res.json();
  $("rows").innerHTML = "";
  if (data.error) { $("msg").textContent = data.error; return; }
  $("msg").textContent = data.results.length ? "" : "No disagreements found.";
  for (const r of data.results) {
    const diff = (r.a_value !== null && r.b_value !== null)
      ? (Number(r.a_value) - Number(r.b_value)).toFixed(2) : "";
    const cells = [r.reason, r.record_id, (r.a_location || "") + " / " + (r.b_location || ""),
                   r.a_value || "", r.b_value || "", diff];
    const tr = document.createElement("tr");
    for (const c of cells) { const td = document.createElement("td"); td.textContent = c; tr.appendChild(td); }
    $("rows").appendChild(tr);
  }
}
$("org").onchange = load;
$("reason").onchange = load;
$("sortcol").onclick = () => { sort = sort === "value" ? "-value" : "value"; load(); };
load();
</script></body></html>"""


def table_page(request):
    return HttpResponse(PAGE)