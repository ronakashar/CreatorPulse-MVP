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
  job_run.py
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

## Scheduled Job (fetch→generate→send)
Run for a user email:
```bash
python -m dotenv -f app/.env run -- python app/job_run.py user@example.com --temperature 0.7 --num-links 5
```

Windows Task Scheduler (Daily 8am):
- Action: Start a program
- Program/script: `powershell`
- Add arguments:
```
-ExecutionPolicy Bypass -Command "cd '<your project path>' ; .\\.venv\\Scripts\\Activate.ps1 ; python -m dotenv -f app/.env run -- python app/job_run.py user@example.com"
```

GitHub Actions (cron example):
```yaml
name: Daily Draft
on:
  schedule:
    - cron: '0 2 * * *'  # 08:00 IST (UTC+5:30) example; adjust per user TZ
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install -r requirements.txt
      - env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          RESEND_API_KEY: ${{ secrets.RESEND_API_KEY }}
          RESEND_FROM: ${{ secrets.RESEND_FROM }}
        run: python app/job_run.py user@example.com --temperature 0.7 --num-links 5
```

## 🚀 Production Deployment

CreatorPulse is now production-ready with comprehensive monitoring, security, and deployment features:

### Production Features
- ✅ **Error Monitoring**: Sentry integration for real-time error tracking
- ✅ **Rate Limiting**: API rate limiting and abuse prevention
- ✅ **Security Hardening**: Input validation, XSS protection, SQL injection prevention
- ✅ **Health Monitoring**: System health checks and performance monitoring
- ✅ **Automated Testing**: Comprehensive test suite for critical components
- ✅ **Docker Deployment**: Production-ready Docker configuration
- ✅ **Backup & Recovery**: Automated backup and disaster recovery procedures

### Deployment Options

#### Docker Deployment
```bash
# Clone repository
git clone https://github.com/yourusername/creatorpulse.git
cd creatorpulse

# Set environment variables
cp .env.example .env
# Edit .env with your production values

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python -c "from services.supabase_client import get_client; print('DB connected')"

# Start application
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
```

### Environment Variables
```bash
# Required for Production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
RESEND_API_KEY=your-resend-api-key
STRIPE_SECRET_KEY=sk_live_your-live-stripe-key
STRIPE_PUBLISHABLE_KEY=pk_live_your-live-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
RESEND_FROM=Your Brand <newsletter@yourdomain.com>

# Monitoring & Security
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
RELEASE_VERSION=1.0.0
SECRET_KEY=your-secret-key-for-sessions
```

### Testing
```bash
# Run test suite
pytest tests/ -v

# Run specific test categories
pytest tests/test_services.py::TestSupabaseClient -v
pytest tests/test_services.py::TestGroqClient -v
pytest tests/test_services.py::TestMonitoringService -v
```

### Monitoring & Health Checks
- **Health Check Endpoint**: `/health` - System status and performance metrics
- **Error Tracking**: Automatic error reporting to Sentry
- **Performance Monitoring**: API response times and system metrics
- **Uptime Monitoring**: Continuous system availability monitoring

### Security Features
- **Input Validation**: All user inputs validated and sanitized
- **Rate Limiting**: Prevents API abuse and brute force attacks
- **SQL Injection Protection**: Parameterized queries and input sanitization
- **XSS Protection**: Content Security Policy and input filtering
- **HTTPS Enforcement**: SSL/TLS encryption for all communications

See `PRODUCTION_CONFIG.md` for detailed production configuration and deployment instructions.

## 📊 Advanced Analytics Dashboard

CreatorPulse includes comprehensive analytics and reporting for Pro and Agency users:

### Usage Analytics
- ✅ **API Usage Tracking**: Monitor Groq API calls, tokens used, and costs
- ✅ **Email Analytics**: Track newsletter sends, open rates, and click-through rates
- ✅ **Content Analytics**: Monitor source fetches, draft generations, and performance
- ✅ **Cost Analysis**: Detailed cost breakdown by service and time period
- ✅ **Usage Trends**: Daily, weekly, and monthly usage patterns

### Reporting Features
- ✅ **Custom Reports**: Generate usage, cost, performance, and engagement reports
- ✅ **Interactive Charts**: Plotly-powered visualizations with drill-down capabilities
- ✅ **Cost Tracking**: Real-time cost monitoring with daily trends
- ✅ **Performance Metrics**: Draft generation times and success rates
- ✅ **Custom Dashboards**: Create and manage personalized analytics dashboards

### Analytics Integration
- ✅ **Automatic Tracking**: All API calls, emails, and user actions are automatically tracked
- ✅ **Real-time Updates**: Analytics update in real-time as you use the platform
- ✅ **Historical Data**: Access historical data for trend analysis
- ✅ **Export Capabilities**: Export analytics data for external analysis

### Plan Requirements
- **Pro Plan ($19/month)**: Access to basic analytics dashboard
- **Agency Plan ($99/month)**: Full analytics suite with custom dashboards and reporting

## 🏢 Agency Dashboard

For agencies managing multiple clients, CreatorPulse includes a comprehensive agency dashboard:

### Multi-Client Management
- ✅ **Client Profiles**: Store client information, contact details, and preferences
- ✅ **Workspace Management**: Create and manage separate workspaces for each client
- ✅ **Team Collaboration**: Invite team members with different roles per workspace
- ✅ **Client Analytics**: Track performance across all client workspaces

### Bulk Operations
- ✅ **Bulk Source Fetching**: Fetch content from all sources across multiple workspaces
- ✅ **Bulk Draft Generation**: Generate newsletter drafts for multiple clients simultaneously
- ✅ **Bulk Newsletter Sending**: Send newsletters to all clients with one click
- ✅ **Operation History**: Track and monitor all bulk operations

### Agency Features
- ✅ **Role-Based Access**: Owner, Admin, Editor, Viewer roles with different permissions
- ✅ **Usage Analytics**: Monitor usage across all workspaces and clients
- ✅ **Billing Management**: Centralized billing for agency subscriptions
- ✅ **CLI Tools**: Command-line tools for automation and scheduled tasks

### CLI Usage
```bash
# Bulk fetch sources for multiple workspaces
python agency_bulk.py fetch --workspace-id <agency-id> --target-workspaces <id1,id2,id3> --created-by user@agency.com

# Bulk generate drafts
python agency_bulk.py generate --workspace-id <agency-id> --target-workspaces <id1,id2,id3> --created-by user@agency.com --temperature 0.7 --num-links 5

# Bulk send newsletters
python agency_bulk.py send --workspace-id <agency-id> --target-workspaces <id1,id2,id3> --created-by user@agency.com
```

## 💳 Stripe Integration

CreatorPulse includes a complete Stripe billing system with subscription plans:

### Subscription Plans
- **Free**: 1 workspace, 5 sources, 10 newsletters/month
- **Pro**: $19/month - 5 workspaces, 50 sources, 100 newsletters/month, analytics
- **Agency**: $99/month - 50 workspaces, 500 sources, 1000 newsletters/month, white-label

### Features
- ✅ Subscription management
- ✅ Usage tracking and limits
- ✅ Stripe Checkout integration
- ✅ Customer portal for billing management
- ✅ Webhook handling for subscription events
- ✅ Plan-based feature restrictions

### Setup
1. Create Stripe account at https://stripe.com
2. Get API keys from Stripe Dashboard
3. Add to `.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
4. Create products and prices in Stripe Dashboard
5. Set up webhook endpoint: `https://your-project.supabase.co/functions/v1/stripe-webhook`

See `STRIPE_SETUP.md` for detailed setup instructions.

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
