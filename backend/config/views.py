from django.db import connections
from django.http import JsonResponse


def _health_status():
    database_ok = False
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            database_ok = cursor.fetchone()[0] == 1
    except Exception:
        # Do not expose database credentials or internal errors publicly.
        database_ok = False

    healthy = database_ok
    return healthy, {
        "status": "ok" if healthy else "unavailable",
        "server": "running",
        "database": "connected" if database_ok else "disconnected",
    }


def health_check(request):
    healthy, payload = _health_status()
    return JsonResponse(payload, status=200 if healthy else 503)


def status_page(request):
    healthy, _ = _health_status()
    colour = "#16a34a" if healthy else "#dc2626"
    title = "All systems operational" if healthy else "Service unavailable"
    database = "Connected successfully" if healthy else "Connection failed"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fridge Refill status</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center;
      font-family: system-ui, sans-serif; background: #f8fafc; color: #0f172a; }}
    main {{ width: min(560px, calc(100% - 32px)); padding: 32px; border-radius: 18px;
      background: white; box-shadow: 0 12px 36px rgba(15, 23, 42, .1); }}
    h1 {{ margin: 0 0 8px; font-size: 1.7rem; }}
    p {{ color: #64748b; margin: 0 0 28px; }}
    .row {{ display: flex; align-items: center; justify-content: space-between;
      padding: 17px 0; border-top: 1px solid #e2e8f0; gap: 16px; }}
    .result {{ display: flex; align-items: center; gap: 9px; font-weight: 650; color: {colour}; }}
    .dot {{ width: 11px; height: 11px; border-radius: 50%; background: {colour};
      box-shadow: 0 0 0 4px {colour}22; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p>Fridge Refill service status</p>
    <div class="row"><span>Web server</span><span class="result"><i class="dot"></i>Running successfully</span></div>
    <div class="row"><span>Database</span><span class="result"><i class="dot"></i>{database}</span></div>
  </main>
</body>
</html>"""
    from django.http import HttpResponse
    return HttpResponse(html, status=200 if healthy else 503)
