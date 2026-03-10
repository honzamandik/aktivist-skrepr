import os
from datetime import datetime, timezone
from aktivist_skrepr.edesky_client import fetch_documents_for_dashboard, fetch_dashboards, filter_dashboards_by_name

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

from datetime import timedelta


def parse_existing_results(path: str):
    """Return (timestamp, set of (dashboard, edesky_id)) from existing HTML.
    If file missing or parse fails, return (None, empty set)."""
    old_set = set()
    ts = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if ts is None and "generated" in line:
                    # look for iso timestamp
                    import re, datetime
                    m = re.search(r"generated (\d{4}-\d{2}-\d{2}T[0-9:.]+)Z", line)
                    if m:
                        ts = datetime.datetime.fromisoformat(m.group(1))
                # rows contain <td>dashboard</td><td>edesky</td>
                if "<tr>" in line and "<td>" in line:
                    parts = [p for p in line.split("<td>") if "</td>" in p]
                    if len(parts) >= 2:
                        try:
                            dash = int(parts[0].split("</td>")[0])
                            eid = parts[1].split("</td>")[0]
                            old_set.add((dash, eid))
                        except ValueError:
                            pass
    except FileNotFoundError:
        pass
    return ts, old_set


def generate(dash_from=59, dash_to=59, api_key=None, keywords=None, created_from=None, name_filter=None):
    api_key = api_key or os.environ.get("EDESKY_API_KEY")
    if not api_key:
        raise SystemExit("Set EDESKY_API_KEY in environment or pass api_key to generate()")
    ensure_out_dir()

    # parse keywords into list; supply default set if none provided
    if keywords is None:
        kw_list = ["cyklo", "opatreni", "uprava", "parkovani", "obousm", "eia"]
    elif isinstance(keywords, str):
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    else:
        kw_list = list(keywords)

    # determine created_from automatically if not provided
    old_ts, old_entries = parse_existing_results(os.path.join(OUT_DIR, "index.html"))
    if created_from is None and old_ts is not None:
        new_from = (old_ts - timedelta(days=50)).date().isoformat()
        created_from = new_from
    # determine dashboard ids to query
    if name_filter:
        all_dash = fetch_dashboards(api_key)
        matched = filter_dashboards_by_name(all_dash, name_filter)
        target_ids = [(int(d.get("edesky_id")), d.get("name")) for d in matched]
    else:
        target_ids = [(i, f"") for i in range(dash_from, dash_to + 1)]

    rows = []
    seen = set()
    # collect results with dashboard metadata
    for did, dname in target_ids:
        for kw in kw_list:
            docs = fetch_documents_for_dashboard(did, api_key, keywords=kw, created_from=created_from)
            for d in docs:
                key = (did, d.get("edesky_id", ""))
                if key in seen:
                    continue
                seen.add(key)
                # pull out attachment name and any included text
                att_name = ""
                att_text = ""
                if d.get("attachments"):
                    first = d["attachments"][0]
                    att_name = first.get("name", "")
                    att_text = first.get("text", "")
                rows.append({
                    "dashboard": did,
                    "dashboard_name": dname,
                    "edesky_id": d.get("edesky_id", ""),
                    "created_at": d.get("created_at", ""),
                    "title": d.get("name", ""),
                    "url": d.get("edesky_url", ""),
                    "attachment": att_name,
                    "attachment_text": att_text,
                })

    # write grouped HTML
    out_path = os.path.normpath(os.path.join(OUT_DIR, "index.html"))
    # prepare a human-readable keywords string for the header
    kw_title = ", ".join(kw_list)
    with open(out_path, "w", encoding="utf-8") as f:
        # basic toggling script for attachment text
        f.write("<!doctype html>\n<html><head><meta charset='utf-8'><title>Edesky results")
        if kw_title:
            f.write(f" ({kw_title})")
        f.write("</title>")
        f.write("<script>function toggle(id){var e=document.getElementById(id);if(e.style.display=='none'){e.style.display='table-row';}else{e.style.display='none';}}</script>")
        f.write("</head><body>")
        # use timezone-aware UTC timestamp to avoid deprecation warnings
        f.write(f"<h1>Edesky results")
        if kw_title:
            f.write(f" ({kw_title})")
        f.write(f" — generated {datetime.now(timezone.utc).isoformat()}Z</h1>\n")

        # group by dashboard
        groups = {}
        for r in rows:
            groups.setdefault((r['dashboard'], r.get('dashboard_name', '')), []).append(r)
        # sort dashboard keys numerically
        for (did, dname) in sorted(groups.keys(), key=lambda x: x[0]):
            f.write(f"<h2>Dashboard {did} {dname}</h2>\n")
            f.write("<table border=1 cellpadding=6>\n")
            f.write("<tr><th>Created</th><th>Edesky ID</th><th>Title</th><th>Attachment</th><th>Text</th><th>URL</th></tr>\n")
            # sort rows by created date string
            for r in sorted(groups[(did, dname)], key=lambda r: r['created_at']):
                is_new = (did, r['edesky_id']) not in old_entries
                if is_new:
                    f.write('<tr style="font-weight:bold">')
                else:
                    f.write("<tr>")
                f.write(f"<td>{r['created_at']}</td>")
                f.write(f"<td>{r['edesky_id']}</td>")
                f.write(f"<td>{r['title']}</td>")
                f.write(f"<td>{r['attachment']}</td>")
                # text toggle button if available
                if r.get('attachment_text'):
                    row_id = f"text-{did}-{r['edesky_id']}"
                    f.write(f"<td><button onclick=\"toggle('{row_id}')\">View</button></td>")
                else:
                    f.write("<td></td>")
                f.write(f"<td><a href=\"{r['url']}\">link</a></td>")
                f.write("</tr>\n")
                # hidden text row
                if r.get('attachment_text'):
                    f.write(f"<tr id=\"{row_id}\" style=\"display:none\"><td colspan=\"6\"><pre>{r['attachment_text']}</pre><br><button onclick=\"toggle('{row_id}')\">Back to table</button></td></tr>\n")
                f.write("</tr>\n")
            f.write("</table>\n")
        f.write("</body></html>")
    print(f"Wrote HTML to {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("generate_docs")
    parser.add_argument("--from", dest="dash_from", type=int, default=59,
                        help="Start dashboard id (ignored if --name-filter is provided)")
    parser.add_argument("--to", dest="dash_to", type=int, default=59,
                        help="End dashboard id (inclusive)")
    parser.add_argument("--keywords", default=None,
                        help="Comma-separated keywords; defaults to a built-in list")
    parser.add_argument("--created-from", dest="created_from", default=None)
    parser.add_argument("--api-key", dest="api_key", default=None)
    parser.add_argument("--name-filter", dest="name_filter", default=None,
                        help="Substring to filter dashboard names (e.g. Praha)")
    args = parser.parse_args()
    generate(dash_from=args.dash_from, dash_to=args.dash_to,
             api_key=args.api_key, keywords=args.keywords,
             created_from=args.created_from, name_filter=args.name_filter)
