"""Schedules today's fact as a Brevo campaign for 08:00 Europe/Sofia."""
import json, os, datetime as dt, urllib.request
from zoneinfo import ZoneInfo
TZ = ZoneInfo("Europe/Sofia")
KEY, LIST, SENDER = os.environ["BREVO_API_KEY"], int(os.environ["BREVO_LIST_ID"]), os.environ["SENDER_EMAIL"]
SITE = os.environ.get("SITE_URL", "https://example.com")

d = json.load(open("facts.json", encoding="utf-8"))
today = dt.datetime.now(TZ).date()
i = (today - dt.date.fromisoformat(d["start"])).days
if not 0 <= i < len(d["facts"]):
    raise SystemExit(f"No fact for {today} (index {i}). Add more facts to facts.json!")
f = d["facts"][i]
when = dt.datetime.combine(today, dt.time(8, 0), TZ)

html = f"""<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:24px;color:#171717">
<p style="color:#686868;font-size:12px;letter-spacing:1px;text-transform:uppercase">Fact #{i+1:03d} · {f['cat']}</p>
<h1 style="font-size:30px;line-height:1.1">{f['title']}</h1>
<p style="font-size:17px;line-height:1.6">{f['body']}</p>
<p style="color:#686868;font-size:13px">Source: {f['source']}</p><hr style="border:0;border-top:1px solid #e5e5df">
<p style="font-size:12px;color:#686868"><a href="{SITE}">OneFactDaily</a> · <a href="{{{{ unsubscribe }}}}">Unsubscribe</a></p></div>"""

def api(path, body):
    r = urllib.request.Request("https://api.brevo.com/v3" + path, json.dumps(body).encode(),
        {"api-key": KEY, "content-type": "application/json", "accept": "application/json"})
    return urllib.request.urlopen(r).read()

print(api("/emailCampaigns", {"name": f"Fact {i+1:03d} {today}", "subject": f"💡 {f['title']}",
    "sender": {"name": "OneFactDaily", "email": SENDER}, "htmlContent": html,
    "recipients": {"listIds": [LIST]}, "scheduledAt": when.isoformat()}))
