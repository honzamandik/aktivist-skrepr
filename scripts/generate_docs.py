import os
from datetime import datetime
from aktivist_skrepr.edesky_client import fetch_documents_for_dashboard, fetch_dashboards, filter_dashboards_by_name

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def generate(dash_from=115, dash_to=121, api_key=None, keywords="cyklo", created_from=None, name_filter=None):
    api_key = api_key or os.environ.get("EDESKY_API_KEY")
    if not api_key:
        raise SystemExit("Set EDESKY_API_KEY in environment or pass api_key to generate()")
    ensure_out_dir()

    # determine dashboard ids to query
    if name_filter:
        all_dash = fetch_dashboards(api_key)
        matched = filter_dashboards_by_name(all_dash, name_filter)
        target_ids = [(int(d.get("edesky_id")), d.get("name")) for d in matched]
    else:
        target_ids = [(i, f"") for i in range(dash_from, dash_to + 1)]

    rows = []
    # collect results with dashboard metadata
    for did, dname in target_ids:
        docs = fetch_documents_for_dashboard(did, api_key, keywords=keywords, created_from=created_from)
        for d in docs:
            rows.append({
                "dashboard": did,
                "dashboard_name": dname,
                "edesky_id": d.get("edesky_id", ""),
                "created_at": d.get("created_at", ""),
                "title": d.get("name", ""),
                "url": d.get("edesky_url", ""),
                "attachment": (d.get("attachments") or [])[0].get("name") if d.get("attachments") else "",
            })

    # write grouped HTML
    out_path = os.path.normpath(os.path.join(OUT_DIR, "index.html"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("<!doctype html>\n<html><head><meta charset='utf-8'><title>Edesky results</title></head><body>")
        f.write(f"<h1>Edesky results — generated {datetime.utcnow().isoformat()}Z</h1>\n")

        # group by dashboard
        groups = {}
        for r in rows:
            groups.setdefault((r['dashboard'], r.get('dashboard_name', '')), []).append(r)
        # sort dashboard keys numerically
        for (did, dname) in sorted(groups.keys(), key=lambda x: x[0]):
            f.write(f"<h2>Dashboard {did} {dname}</h2>\n")
            f.write("<table border=1 cellpadding=6>\n")
            f.write("<tr><th>Created</th><th>Edesky ID</th><th>Title</th><th>Attachment</th><th>URL</th></tr>\n")
            # sort rows by created date string
            for r in sorted(groups[(did, dname)], key=lambda r: r['created_at']):
                f.write("<tr>")
                f.write(f"<td>{r['created_at']}</td>")
                f.write(f"<td>{r['edesky_id']}</td>")
                f.write(f"<td>{r['title']}</td>")
                f.write(f"<td>{r['attachment']}</td>")
                f.write(f"<td><a href=\"{r['url']}\">link</a></td>")
                f.write("</tr>\n")
            f.write("</table>\n")
        f.write("</body></html>")
    print(f"Wrote HTML to {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("generate_docs")
    parser.add_argument("--from", dest="dash_from", type=int, default=115,
                        help="Start dashboard id (ignored if --name-filter is provided)")
    parser.add_argument("--to", dest="dash_to", type=int, default=121,
                        help="End dashboard id (inclusive)")
    parser.add_argument("--keywords", default="cyklo")
    parser.add_argument("--created-from", dest="created_from", default=None)
    parser.add_argument("--api-key", dest="api_key", default=None)
    parser.add_argument("--name-filter", dest="name_filter", default=None,
                        help="Substring to filter dashboard names (e.g. Praha)")
    args = parser.parse_args()
    generate(dash_from=args.dash_from, dash_to=args.dash_to,
             api_key=args.api_key, keywords=args.keywords,
             created_from=args.created_from, name_filter=args.name_filter)
