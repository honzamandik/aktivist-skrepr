import os
from datetime import datetime, timezone
from aktivist_skrepr.edesky_client import fetch_documents_for_dashboard, fetch_dashboards, filter_dashboards_by_name

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

from datetime import timedelta
import html
import re


def escape_html(value: str):
    return html.escape(value or "", quote=False)


def highlight_text(value: str, terms):
    if not value:
        return ""
    safe = escape_html(value)
    def repl(match):
        return f"<mark>{match.group(0)}</mark>"
    for t in sorted(terms, key=len, reverse=True):
        if not t:
            continue
        try:
            safe = re.sub(r"(?i)" + re.escape(t), repl, safe)
        except re.error:
            continue
    return safe


def parse_existing_results(path: str):
    """Return (timestamp, set of edesky IDs) from existing HTML.
    If file missing or parse fails, return (None, empty set)."""
    old_set = set()
    ts = None
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        import re
        # parse generated timestamp from header
        m = re.search(r"generated (\d{4}-\d{2}-\d{2}T[0-9:.]+)Z", text)
        if m:
            ts = datetime.fromisoformat(m.group(1))
        # find all table rows and collect Edesky IDs from second <td>
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", text, flags=re.S | re.I):
            cells = re.findall(r"<td>(.*?)</td>", row, flags=re.S | re.I)
            if len(cells) >= 2:
                eid = cells[1].strip()
                if eid:
                    old_set.add(eid)
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
        # reduced default set per user request
        kw_list = ["cyklo", "navrh"]
    elif isinstance(keywords, str):
        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    else:
        kw_list = list(keywords)

    # determine created_from automatically if not provided
    old_ts, old_entries = parse_existing_results(os.path.join(OUT_DIR, "index.html"))
    if created_from is None and old_ts is not None:
        new_from = (old_ts - timedelta(days=30)).date().isoformat()
        created_from = new_from
    # determine dashboard ids to query
    if name_filter:
        all_dash = fetch_dashboards(api_key)
        matched = filter_dashboards_by_name(all_dash, name_filter)
        target_ids = [(int(d.get("edesky_id")), d.get("name")) for d in matched]
    else:
        target_ids = [(i, f"") for i in range(dash_from, dash_to + 1)]

    rows = {}
    # collect results with dashboard metadata
    for did, dname in target_ids:
        # skip dashboard 59 per user request
        if did == 59:
            continue
        for kw in kw_list:
            docs = fetch_documents_for_dashboard(did, api_key, keywords=kw, created_from=created_from)
            for d in docs:
                key = (did, d.get("edesky_id", ""))
                # pull out attachment name and any included text
                att_name = ""
                att_text = ""
                if d.get("attachments"):
                    first = d["attachments"][0]
                    att_name = first.get("name", "")
                    att_text = first.get("text", "")
                if key not in rows:
                    rows[key] = {
                        "dashboard": did,
                        "dashboard_name": dname,
                        "edesky_id": d.get("edesky_id", ""),
                        "created_at": d.get("created_at", ""),
                        "title": d.get("name", ""),
                        "url": d.get("edesky_url", ""),
                        "attachment": att_name,
                        "attachment_text": att_text,
                        "found_keywords": set(),
                        "found_text_keywords": [],
                    }
                row = rows[key]
                row["found_keywords"].add(kw)

    # convert rows dict to list for ordered iteration
    rows = list(rows.values())

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
            f.write("<tr><th>Datum vytvoření</th><th>Edesky ID</th><th>Název zápisu</th><th>Vyhledaná klíčová slova</th><th>Relevantní pro cyklistiku</th><th>Nalezené cyklistické výrazy v textu</th><th>Příloha</th><th>Text přílohy</th><th>Odkaz</th></tr>\n")
            # sort rows by created date string
            for r in sorted(groups[(did, dname)], key=lambda r: r['created_at']):
                is_new = r['edesky_id'] not in old_entries
                if is_new:
                    f.write('<tr style="font-weight:bold">')
                else:
                    f.write("<tr>")

                found_keywords = sorted(r.get('found_keywords', []))
                found_text = ", ".join(found_keywords)
                # determine cycling relevance from text/title
                text_to_check = " ".join([r.get('title', ''), r.get('attachment_text', '')]).lower()
                cycling_terms = [
                    "cyklopruh", "cyklo", "cyklist", "cykloobousmerky", "e 12b", "ochrany pruh", "pruh pro cyklo", "cyklistick",
                    "c8a stezka pro cyklisty", "c8b konec stezky pro cyklisty", "c9a stezka pro chodce a cyklisty", "c9b konec stezky pro chodce a cyklisty",
                    "c10a stezka pro chodce a cyklisty (dělená)", "c10b konec stezky pro chodce a cyklisty (dělené)", "ip7 přejezd pro cyklisty",
                    "a19 cyklisté", "b8 zákaz vjezdu jízdních kol", "ip4c protisměrný pruh pro cyklisty", "is19 směrová tabule pro cyklisty",
                    "is20 návěst před křižovatkou pro cyklisty", "is21 směrová tabulka pro cyklisty", "is22 směrová tabulka pro cyklisty"
                ]
                found_text_keywords = [term for term in cycling_terms if term in text_to_check]
                found_text_terms = ", ".join(found_text_keywords)
                cycling_relevant = len(found_text_keywords) > 0

                f.write(f"<td>{escape_html(r['created_at'])}</td>")
                f.write(f"<td>{escape_html(r['edesky_id'])}</td>")
                f.write(f"<td>{escape_html(r['title'])}</td>")
                f.write(f"<td>{escape_html(found_text)}</td>")
                f.write(f"<td>{'true' if cycling_relevant else 'false'}</td>")
                f.write(f"<td>{escape_html(found_text_terms if cycling_relevant else '')}</td>")
                f.write(f"<td>{escape_html(r['attachment'])}</td>")
                # text toggle button if available
                if r.get('attachment_text'):
                    row_id = f"text-{did}-{r['edesky_id']}"
                    f.write(f"<td><button onclick=\"toggle('{row_id}')\">Zobrazit</button></td>")
                else:
                    f.write("<td></td>")
                f.write(f"<td><a href=\"{escape_html(r['url'])}\">odkaz</a></td>")
                f.write("</tr>\n")
                # hidden text row
                if r.get('attachment_text'):
                    highlighted = highlight_text(r['attachment_text'], found_text_keywords)
                    f.write(f"<tr id=\"{row_id}\" style=\"display:none\"><td colspan=\"9\"><pre>{highlighted}</pre><br><button onclick=\"toggle('{row_id}')\">Zpět</button></td></tr>\n")
            f.write("</table>\n")
        f.write("</body>")
        # insert pagination warning paragraph if any
        from aktivist_skrepr import edesky_client
        if edesky_client.pagination_warnings:
            f.write("<p><strong>Note:</strong> pagination disabled for dashboards: ")
            parts = [f"{did} ({total} pages)" for did, total in edesky_client.pagination_warnings]
            f.write(", ".join(parts))
            f.write(".</p>\n")
        f.write("</html>")
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
