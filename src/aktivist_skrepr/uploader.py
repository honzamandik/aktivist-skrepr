import os
import requests
from typing import List

def post_to_webhook(webhook_url: str, links: List[str]) -> bool:
    payload = {"links": links}
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    return True

def append_to_google_sheet(service_account_path: str, spreadsheet_key: str, values: List[List[str]]):
    # Placeholder: implement using gspread and service account
    raise NotImplementedError("Google Sheets upload not implemented in scaffold. Use gspread with a service account.")
