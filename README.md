# CreatorPulse MVP

AI-powered daily feed curator and newsletter generator for creators.

- Frontend: Streamlit
- Backend & DB: Supabase
- AI: Groq (Llama 3)
- Email: Resend
- Language: Python

## Features
- Supabase Auth: signup/login/logout
- Source management: Twitter (X), YouTube, RSS
- Content fetching: snscrape, yt-dlp, feedparser (+ fallbacks)
- Style upload: .txt/.csv to Supabase Storage
- Draft generation: Groq Llama 3, style-conditioned
- Review, inline edit, and send via Resend
- Save drafts, feedback, and sent state in Supabase

## Structure
```
app/
  main.py
  pages/
    1_Dashboard.py
    2_Sources.py
    3_Style_Upload.py
    4_Settings.py
  services/
    supabase_client.py
    groq_client.py
    resend_client.py
    content_fetcher.py
    newsletter_generator.py
  utils/
    formatting.py
    ui.py
.streamlit/config.toml
requirements.txt
supabase_schema.sql
```

## Setup
1) Create venv and install
```bash
python -m venv .venv
# PowerShell
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```
2) Env vars in `app/.env`
```
SUPABASE_URL=
SUPABASE_KEY=
GROQ_API_KEY=
RESEND_API_KEY=
RESEND_FROM=Acme <onboarding@resend.dev>
```
3) Supabase
- Run `supabase_schema.sql` in SQL editor
- Create public bucket `style-samples`

## Run
```bash
python -m dotenv -f app/.env run -- streamlit run app/main.py
```

## Usage
- Add sources (Twitter handle/URL, YouTube channel/feeds, RSS)
- Upload style samples (.txt/.csv)
- Dashboard: Fetch → select items → set creativity/links → Generate
- Edit draft → Send via email

## Notes
- Twitter falls back to multiple Nitter mirrors and HTML proxy if needed
- YouTube supports channel feeds and @handles (auto `/videos` for yt-dlp)

## Troubleshooting
- If email 403 domain not verified: use `RESEND_FROM=Acme <onboarding@resend.dev>` locally
- If Twitter still 0 items, try an RSS to confirm pipeline

## License
MIT
