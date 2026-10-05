"""Schedules today's fact as a Brevo campaign for 08:00 Europe/Sofia."""
import json, os, datetime as dt, urllib.request, urllib.error
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

html = f"""<!doctype html>
<html>
<body style="margin:0;padding:0;background:#f7f7f4;color:#171717;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f7f7f4">
<tr><td align="center" style="padding:28px 14px">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:680px">
<tr><td style="padding:4px 4px 20px;font-size:18px;font-weight:700;letter-spacing:-.5px">OneFactDaily</td></tr>
<tr><td style="background:#ffffff;border:1px solid #e5e5df;border-radius:24px;padding:38px 34px">
<p style="margin:0;color:#686868;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase">Fact #{i+1:03d} · {f['cat']} <span style="float:right">30 SEC READ</span></p>
<h1 style="margin:30px 0 22px;font-size:42px;line-height:1.05;letter-spacing:-1.5px;font-weight:700">{f['title']}</h1>
<p style="margin:0;font-size:18px;line-height:1.65;color:#454545">{f['body']}</p>
<p style="margin:30px 0 0;color:#686868;font-size:13px">Source: {f['source']}</p>
<hr style="border:0;border-top:1px solid #e5e5df;margin:28px 0">
<a href="{SITE}" style="display:inline-block;color:#171717;font-size:16px;text-decoration:underline">Browse today's fact →</a>
</td></tr>
<tr><td style="padding:22px 4px 4px;color:#686868;font-size:12px;line-height:1.6">
<a href="{SITE}" style="color:#686868;text-decoration:none">OneFactDaily</a> · <a href="{{{{ unsubscribe }}}}" style="color:#686868">Unsubscribe</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

def api(path, body):
    r = urllib.request.Request("https://api.brevo.com/v3" + path, json.dumps(body).encode(),
        {"api-key": KEY, "content-type": "application/json", "accept": "application/json"})
    try:
        return urllib.request.urlopen(r).read()
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Brevo API error {e.code}: {details}") from None

print(api("/emailCampaigns", {"name": f"Fact {i+1:03d} {today}", "subject": f"💡 {f['title']}",
    "sender": {"name": "OneFactDaily", "email": SENDER}, "htmlContent": html,
    "recipients": {"listIds": [LIST]}, "scheduledAt": when.isoformat()}))
