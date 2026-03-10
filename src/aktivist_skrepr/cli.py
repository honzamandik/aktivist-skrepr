import argparse
import os
from .fetcher import fetch_url
from .filterer import extract_links, filter_links_by_keywords
from .uploader import post_to_webhook

def main(argv=None):
    parser = argparse.ArgumentParser("aktivist-skrepr")
    parser.add_argument("--url", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--webhook", required=False)
    args = parser.parse_args(argv)

    html = fetch_url(args.url)
    links = extract_links(html, args.url)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    picked = filter_links_by_keywords(links, keywords)

    if args.webhook:
        post_to_webhook(args.webhook, picked)
        print(f"Posted {len(picked)} links to webhook")
    else:
        print("Picked links:")
        for l in picked:
            print(l)

if __name__ == "__main__":
    main()
