# aktivist-skrepr

Lightweight Python app to fetch documents, pick relevant ones by keywords, and post links to Google Sheets or a custom website/webhook.

Quick start
1. Open a PowerShell terminal in the project root.
2. Run the setup script to create a venv and install dependencies:

   .\scripts\setup_env.ps1

3. Create a `.env` file (see `.env.sample`) and set any credentials (Google service account path, webhook URL).

Run the CLI on a single URL:

   python -m aktivist_skrepr.cli --url "https://example.com" --keywords "climate,policy" --webhook "https://example.org/webhook"

Run tests:

   pytest -q

Connecting to GitHub
1. Initialize git, commit, and push to a new GitHub repo you create (or use the GitHub UI/gh CLI):

   git init
   git add .
   git commit -m "Initial scaffold"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main

See the "How it works" and "Notes" sections below for details.

How it works
- `src/aktivist_skrepr/fetcher.py`: fetch pages (requests).
- `src/aktivist_skrepr/filterer.py`: extract links and filter by keywords (BeautifulSoup).
- `src/aktivist_skrepr/uploader.py`: helpers to post to a webhook or append to Google Sheets (gspread).
- `src/aktivist_skrepr/cli.py`: small CLI glue.

Notes
- Google Sheets: use a service account JSON and set `GOOGLE_APPLICATION_CREDENTIALS` to its path or provide the path via `.env`.
- This scaffold uses placeholders for sensitive credentials—never commit secrets.
