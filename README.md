# aktivist-skrepr

Lightweight Python app to fetch documents, pick relevant ones by keywords, and post links to Google Sheets or a custom website/webhook.

Quick start
1. Open a PowerShell terminal in the project root.
2. Run the setup script to create a venv and install dependencies:

   .\scripts\setup_env.ps1

   # optionally install the package into the environment for CLI use
   pip install -e .

3. Create a `.env` file (see `.env.sample`) and set any credentials (Google service account path, webhook URL).

Run the CLI on a single URL:

   python -m aktivist_skrepr.cli --url "https://example.com" --keywords "climate,policy" --webhook "https://example.org/webhook"

Run tests:

   pytest -q

Run Edesky fetch (dashboards 115-121)

1. Set your API key in the environment (PowerShell):

   $env:EDESKY_API_KEY = "Rv5pKLg20UI1clhppns26ZOxvOg9MvEf"

2. Run the CLI in edesky mode:

   python -m aktivist_skrepr.cli --edesky --edesky-from 115 --edesky-to 121 --keywords cyklo --created-from 2026-01-24

The script will print a simple table of found documents to the terminal.

Publish results to GitHub Pages

Two options:

1) Manual: generate `docs/index.html` locally and push to the `main` branch. GitHub Pages can serve the `docs/` folder.

   - Generate:

       python .\scripts\generate_docs.py --from 115 --to 121 --keywords cyklo --created-from 2026-01-24

   - Commit and push `docs/index.html` to `main` and enable Pages in repo Settings > Pages > Source: Deploy from a branch > `main`/`/docs`.

2) Automatic: use the provided GitHub Action `publish-pages.yml` which runs on push and deploys `docs/` to Pages.

   Steps to enable automatic publishing:
   - Create a GitHub repo and push this project (see previous instructions).
   - In GitHub repo settings, ensure GitHub Pages is enabled for the repository.
   - Add a repository secret named `EDESKY_API_KEY` with your API key (Settings > Secrets and variables > Actions > New repository secret).
   - Push to `main`/`master`. The workflow will run, generate `docs/index.html`, and publish it.



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
