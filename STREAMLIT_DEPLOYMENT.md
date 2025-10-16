# Streamlit Cloud Environment Variables Setup

## For Local Development:
1. Create a `.env` file in your project root
2. Add your API keys to the `.env` file

## For Streamlit Cloud Deployment:

### Method 1: Streamlit Cloud Secrets (Recommended)
1. Go to your Streamlit Cloud dashboard
2. Click on your app
3. Go to "Settings" → "Secrets"
4. Add the following secrets:

```toml
[secrets]
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_KEY = "your_supabase_anon_key_here"
GROQ_API_KEY = "your_groq_api_key_here"
RESEND_API_KEY = "your_resend_api_key_here"
STRIPE_SECRET_KEY = "your_stripe_secret_key_here"
STRIPE_PUBLISHABLE_KEY = "your_stripe_publishable_key_here"
RESEND_FROM = "Acme <onboarding@resend.dev>"
SENTRY_DSN = "your_sentry_dsn_here"
REDIS_URL = "your_redis_url_here"
```

### Method 2: Environment Variables
1. Go to your Streamlit Cloud dashboard
2. Click on your app
3. Go to "Settings" → "Environment Variables"
4. Add each variable individually:
   - SUPABASE_URL
   - SUPABASE_KEY
   - GROQ_API_KEY
   - RESEND_API_KEY
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLISHABLE_KEY
   - RESEND_FROM
   - SENTRY_DSN
   - REDIS_URL

## Required API Keys:

### 1. Supabase
- Go to https://supabase.com
- Create a new project
- Get URL and anon key from Settings → API

### 2. Groq
- Go to https://console.groq.com
- Create an account and get API key

### 3. Resend
- Go to https://resend.com
- Create an account and get API key

### 4. Stripe (Optional)
- Go to https://stripe.com
- Create an account and get API keys

## After Adding Secrets:
1. Restart your Streamlit Cloud app
2. The app should now load without environment variable errors
