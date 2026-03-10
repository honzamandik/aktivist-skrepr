import argparse
import os
from textwrap import shorten
from .fetcher import fetch_url
from .filterer import extract_links, filter_links_by_keywords
from .uploader import post_to_webhook
from .edesky_client import fetch_documents_for_dashboard, fetch_dashboards, filter_dashboards_by_name


def main(argv=None):
    parser = argparse.ArgumentParser("aktivist-skrepr")
    parser.add_argument("--url", required=False, help="URL to fetch (not required for --edesky)")
    # default keywords include the core term plus additional Czech terms
    parser.add_argument("--keywords", default="cyklo,parkovani",
                        help="Comma-separated keywords (default: cyklo and parkovani)")
    parser.add_argument("--webhook", required=False, help="Webhook URL to post picked links")

    # Edesky mode flags
    parser.add_argument("--edesky", action="store_true", help="Use Edesky API mode")
    parser.add_argument("--edesky-from", dest="edesky_from", type=int, default=59, help="Start dashboard id (inclusive)")
    parser.add_argument("--edesky-to", dest="edesky_to", type=int, default=59, help="End dashboard id (inclusive)")
    parser.add_argument("--created-from", dest="created_from", default=None, help="created_from date YYYY-MM-DD")
    parser.add_argument("--dashboard-name-filter", dest="name_filter", default=None, help="Substring to choose dashboards by name (e.g. Praha)")

    args = parser.parse_args(argv)

    if args.edesky:
        api_key = os.environ.get("EDESKY_API_KEY")
        if not api_key:
            print("Set EDESKY_API_KEY in environment to use edesky mode")
            return
        if args.name_filter:
            all_dash = fetch_dashboards(api_key)
            matched = filter_dashboards_by_name(all_dash, args.name_filter)
            dashboards = [int(d.get("edesky_id")) for d in matched]
        else:
            dashboards = list(range(args.edesky_from, args.edesky_to + 1))
        kw_list = [k.strip() for k in args.keywords.split(",") if k.strip()]
        rows = []
        seen = set()
        for did in dashboards:
            for kw in kw_list:
                docs = fetch_documents_for_dashboard(did, api_key, keywords=kw, created_from=args.created_from)
                for d in docs:
                    edesky_id = d.get("edesky_id") or ""
                    if (did, edesky_id) in seen:
                        continue
                    seen.add((did, edesky_id))
                    title = d.get("name") or ""
                    created = d.get("created_at") or ""
                    url = d.get("edesky_url") or ""
                    first_att = (d.get("attachments") or [])[0].get("name") if d.get("attachments") else ""
                    rows.append((did, edesky_id, created, shorten(title, width=50), first_att, url))
        # sort by dashboard then created
        rows.sort(key=lambda r: (r[0], r[2]))

        # print ascii table with keywords used
        kw_title = ", ".join(kw_list)
        print("\nEdesky results" + (f" ({kw_title})" if kw_title else ""))
        print("Dash | EdeskID | Created | Title | Attachment | URL")
        for r in rows:
            print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]}")
        return

    # non-edesky flow requires URL
    if not args.url:
        parser.error("--url is required unless --edesky is used")

    html = fetch_url(args.url)
    links = extract_links(html, args.url)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    picked = filter_links_by_keywords(links, keywords)

    if args.webhook:
        post_to_webhook(args.webhook, picked)
        print(f"Posted {len(picked)} links to webhook")
    else:
        print("Picked links:")
        print("URL")
        for l in picked:
            print(l)


if __name__ == "__main__":
    main()
