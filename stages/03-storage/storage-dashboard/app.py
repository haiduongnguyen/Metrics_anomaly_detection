import os
import json
import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

STORAGE_ROUTER_URL = os.getenv("STORAGE_ROUTER_URL", "http://storage-router:8030")
LIFECYCLE_URL = os.getenv("LIFECYCLE_URL", "http://lifecycle-manager:8031")
REFRESH_MS = int(os.getenv("REFRESH_MS", "2000"))

app = FastAPI(title="Stage 03 - Storage Dashboard", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "storage-dashboard"}

@app.get("/api/stats")
def api_stats():
    data = {
        "storage_router": {"ok": False},
        "lifecycle": {"ok": False},
        "refresh_ms": REFRESH_MS,
    }
    # Storage router stats
    try:
        r = requests.get(f"{STORAGE_ROUTER_URL}/stats", timeout=3)
        r.raise_for_status()
        sr = r.json()
        data["storage_router"] = {"ok": True, **sr}
    except Exception as e:
        data["storage_router"] = {"ok": False, "error": str(e)}

    # Lifecycle stats
    try:
        r = requests.get(f"{LIFECYCLE_URL}/stats", timeout=3)
        r.raise_for_status()
        lf = r.json()
        data["lifecycle"] = {"ok": True, **lf}
    except Exception as e:
        data["lifecycle"] = {"ok": False, "error": str(e)}

    return JSONResponse(data)

@app.get("/")
def index():
    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Stage 03 - Storage Dashboard</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji'; background:#0b1220; color:#e5e7eb; margin:0; }}
    header {{ padding:16px 20px; background:#0f172a; border-bottom:1px solid #1f2937; }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap:16px; padding:20px; }}
    .card {{ background:#111827; border:1px solid #1f2937; border-radius:10px; padding:16px; }}
    .title {{ font-size:18px; margin:0 0 8px 0; color:#93c5fd; }}
    .kpi {{ font-size:28px; margin:6px 0; color:#f9fafb; }}
    .ok {{ color:#22c55e; }} .bad {{ color:#ef4444; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size:12px; color:#9ca3af; }}
    .footer {{ padding:10px 20px; border-top:1px solid #1f2937; color:#9ca3af; font-size:12px; }}
    .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #374151; background:#0b1220; color:#d1d5db; font-size:12px; margin-left:8px; }}
  </style>
</head>
<body>
  <header>
    <h2 style="display:flex;align-items:center;gap:8px;">Stage 03 - Storage Dashboard <span class="pill">Refresh {REFRESH_MS} ms</span></h2>
  </header>
  <div class="grid">
    <div class="card">
      <div class="title">Storage Router</div>
      <div id="sr-status" class="mono">status: ...</div>
      <div class="kpi"><span id="sr-warm">-</span> warm objects</div>
      <div class="mono">Cold objects mirror: <span id="sr-cold">-</span></div>
      <div class="mono">Redis keys: <span id="sr-redis">-</span></div>
      <div class="mono">Last route epoch: <span id="sr-last">-</span></div>
    </div>
    <div class="card">
      <div class="title">Lifecycle Manager</div>
      <div id="lf-status" class="mono">status: ...</div>
      <div class="kpi"><span id="lf-cold">-</span> cold objects</div>
      <div class="mono">Warm objects: <span id="lf-warm">-</span></div>
      <div class="mono">Policy: cold ≥ <span id="lf-cold-days">-</span>d, archive ≥ <span id="lf-archive-days">-</span>d</div>
      <div class="mono">Last cycle epoch: <span id="lf-last">-</span></div>
    </div>
    <div class="card">
      <div class="title">Raw JSON</div>
      <pre id="raw" class="mono" style="white-space:pre-wrap;word-break:break-word;">loading...</pre>
    </div>
  </div>
  <div class="footer">Stage 03 - Multi-tier storage (Hot/Warm/Cold) • LocalStack S3 + Redis</div>
  <script>
    async function refresh() {{
      try {{
        const r = await fetch('/api/stats');
        const data = await r.json();
        document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
        // Storage Router
        const srOk = data.storage_router?.ok;
        document.getElementById('sr-status').innerHTML = 'status: ' + (srOk ? '<span class="ok">OK</span>' : '<span class="bad">DOWN</span>');
        document.getElementById('sr-warm').textContent = data.storage_router?.warm_objects ?? '-';
        document.getElementById('sr-cold').textContent = data.storage_router?.cold_objects ?? '-';
        document.getElementById('sr-redis').textContent = data.storage_router?.redis_keys ?? '-';
        document.getElementById('sr-last').textContent = data.storage_router?.last_route_epoch ?? '-';
        // Lifecycle
        const lfOk = data.lifecycle?.ok;
        document.getElementById('lf-status').innerHTML = 'status: ' + (lfOk ? '<span class="ok">OK</span>' : '<span class="bad">DOWN</span>');
        document.getElementById('lf-cold').textContent = data.lifecycle?.cold_objects ?? '-';
        document.getElementById('lf-warm').textContent = data.lifecycle?.warm_objects ?? '-';
        document.getElementById('lf-cold-days').textContent = data.lifecycle?.cold_after_days ?? '-';
        document.getElementById('lf-archive-days').textContent = data.lifecycle?.archive_after_days ?? '-';
        document.getElementById('lf-last').textContent = data.lifecycle?.last_cycle_epoch ?? '-';
      }} catch (e) {{
        document.getElementById('raw').textContent = 'Fetch error: ' + e;
      }} finally {{
        setTimeout(refresh, {REFRESH_MS});
      }}
    }}
    refresh();
  </script>
</body>
</html>
"""
    return HTMLResponse(html)