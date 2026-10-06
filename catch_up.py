"""Sends today's fact (as a Brevo campaign, with unsubscribe) to people who joined after 08:00."""
import json, os, datetime as dt, urllib.request, urllib.error, urllib.parse
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Sofia")
KEY, LIST, SENDER = os.environ["BREVO_API_KEY"], int(os.environ["BREVO_LIST_ID"]), os.environ["SENDER_EMAIL"]
SITE = os.environ.get("SITE_URL", "https://example.com")

now = dt.datetime.now(TZ)
today = now.date()
cutoff = dt.datetime.combine(today, dt.time(8, 0), TZ)
if now < cutoff:
    raise SystemExit("Before 08:00: the daily campaign will reach everyone.")

d = json.load(open("facts.json", encoding="utf-8"))
i = (today - dt.date.fromisoformat(d["start"])).days
if not 0 <= i < len(d["facts"]):
    raise SystemExit(f"No fact for {today}.")
f = d["facts"][i]
subject = f"💡 {f['title']}"

html = f"""<!doctype html><html><body style="margin:0;background:#f7f7f4;font-family:Arial,sans-serif;color:#171717">
<div style="max-width:620px;margin:auto;padding:28px 14px">
<p style="font-size:18px;font-weight:700;margin:0 0 18px">OneFactDaily</p>
<div style="background:#fff;border:1px solid #e5e5df;border-radius:20px;padding:32px 28px">
<p style="margin:0 0 6px;color:#686868;font-size:12px;letter-spacing:1.5px;text-transform:uppercase">Welcome! Today's fact · #{i+1:03d} · {f['cat']}</p>
<h1 style="margin:22px 0 18px;font-size:34px;line-height:1.1">{f['title']}</h1>
<p style="margin:0;font-size:17px;line-height:1.6;color:#454545">{f['body']}</p>
<p style="margin:24px 0 0;color:#686868;font-size:13px">Source: {f['source']}</p></div>
<p style="color:#686868;font-size:12px;line-height:1.6">You just subscribed to <a href="{SITE}" style="color:#686868">OneFactDaily</a>. Tomorrow your first fact arrives at 8:00. <a href="{{{{ unsubscribe }}}}" style="color:#686868">Unsubscribe</a></p>
</div></body></html>"""

def api(method, path, body=None):
    r = urllib.request.Request("https://api.brevo.com/v3" + path,
        json.dumps(body).encode() if body is not None else None,
        {"api-key": KEY, "content-type": "application/json", "accept": "application/json"}, method=method)
    try:
        return json.loads(urllib.request.urlopen(r).read() or b"{}")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Brevo API error {e.code}: {e.read().decode('utf-8', 'replace')}") from None

def paged(path, key):
    out, off = [], 0
    while True:
        sep = "&" if "?" in path else "?"
        r = api("GET", f"{path}{sep}limit=50&offset={off}").get(key, [])
        out += r
        if len(r) < 50:
            return out
        off += 50

def list_id(name):
    for l in paged("/contacts/lists", "lists"):
        if l["name"] == name:
            return l["id"]
    folder = api("GET", "/contacts/folders?limit=1").get("folders", [{}])[0].get("id", 1)
    return api("POST", "/contacts/lists", {"name": name, "folderId": folder})["id"]

since = cutoff.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
q = urllib.parse.urlencode({"createdSince": since, "limit": 500})
contacts = api("GET", f"/contacts/lists/{LIST}/contacts?{q}").get("contacts", [])
day_id = list_id(f"catchup-{today}")
done = {c["email"].lower() for c in api("GET", f"/contacts/lists/{day_id}/contacts?limit=500").get("contacts", [])}

new = []
for c in contacts:
    if c.get("emailBlacklisted") or c["email"].lower() in done:
        continue
    created = dt.datetime.fromisoformat(c["createdAt"].replace("Z", "+00:00"))
    if created >= cutoff:
        new.append(c["email"])
if not new:
    raise SystemExit("No new subscribers to catch up.")

tmp_id = list_id(f"catchup-{today}-{now:%H%M}")
for ids in (day_id, tmp_id):
    for k in range(0, len(new), 100):
        api("POST", f"/contacts/lists/{ids}/contacts/add", {"emails": new[k:k+100]})

camp = api("POST", "/emailCampaigns", {"name": f"Catch-up {i+1:03d} {today} {now:%H%M}", "subject": subject,
    "sender": {"name": "OneFactDaily", "email": SENDER}, "htmlContent": html, "recipients": {"listIds": [tmp_id]}})
api("POST", f"/emailCampaigns/{camp['id']}/sendNow")
print(f"Sent today's fact to {len(new)} new subscriber(s).")
