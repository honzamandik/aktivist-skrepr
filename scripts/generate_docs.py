import os
from datetime import datetime
from aktivist_skrepr.edesky_client import fetch_documents_for_dashboard

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def generate(dash_from=115, dash_to=121, api_key=None, keywords="cyklo", created_from=None):
    api_key = api_key or os.environ.get("EDESKY_API_KEY")
    if not api_key:
        raise SystemExit("Set EDESKY_API_KEY in environment or pass api_key to generate()")
    ensure_out_dir()
    rows = []
    for did in range(dash_from, dash_to + 1):
        docs = fetch_documents_for_dashboard(did, api_key, keywords=keywords, created_from=created_from)
        for d in docs:
            rows.append({
                "dashboard": did,
                "edesky_id": d.get("edesky_id", ""),
                "created_at": d.get("created_at", ""),
                "title": d.get("name", ""),
                "url": d.get("edesky_url", ""),
                "attachment": (d.get("attachments") or [])[0].get("name") if d.get("attachments") else "",
            })

    # write simple HTML
    out_path = os.path.normpath(os.path.join(OUT_DIR, "index.html"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("<!doctype html>\n<html><head><meta charset='utf-8'><title>Edesky results</title></head><body>")
        f.write(f"<h1>Edesky results — generated {datetime.utcnow().isoformat()}Z</h1>\n")
        f.write("<table border=1 cellpadding=6>\n")
        f.write("<tr><th>Dashboard</th><th>Edesky ID</th><th>Created</th><th>Title</th><th>Attachment</th><th>URL</th></tr>\n")
        for r in rows:
            f.write("<tr>")
            f.write(f"<td>{r['dashboard']}</td>")
            f.write(f"<td>{r['edesky_id']}</td>")
            f.write(f"<td>{r['created_at']}</td>")
            f.write(f"<td>{r['title']}</td>")
            f.write(f"<td>{r['attachment']}</td>")
            f.write(f"<td><a href=\"{r['url']}\">link</a></td>")
            f.write("</tr>\n")
        f.write("</table></body></html>")
    print(f"Wrote HTML to {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("generate_docs")
    parser.add_argument("--from", dest="dash_from", type=int, default=115)
    parser.add_argument("--to", dest="dash_to", type=int, default=121)
    parser.add_argument("--keywords", default="cyklo")
    parser.add_argument("--created-from", dest="created_from", default=None)
    parser.add_argument("--api-key", dest="api_key", default=None)
    args = parser.parse_args()
    generate(dash_from=args.dash_from, dash_to=args.dash_to, api_key=args.api_key, keywords=args.keywords, created_from=args.created_from)
