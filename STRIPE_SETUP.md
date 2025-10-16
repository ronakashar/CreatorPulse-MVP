# Stripe Integration Setup Guide

## 🔧 Environment Variables

Add these to your `.env` file:

```bash
# Stripe Test Keys (for development)
STRIPE_SECRET_KEY=sk_test_your_test_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Optional: Stripe Live Keys (for production)
# STRIPE_SECRET_KEY=sk_live_your_live_secret_key
# STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
# STRIPE_WEBHOOK_SECRET=whsec_your_live_webhook_secret
```

## 📋 Setup Steps

### 1. Create Stripe Account
- Go to https://stripe.com
- Create account (free)
- Complete business verification (for live mode)

### 2. Get API Keys
- Go to Stripe Dashboard → Developers → API Keys
- Copy **Publishable key** (starts with `pk_test_`)
- Copy **Secret key** (starts with `sk_test_`)

### 3. Create Products & Prices
In Stripe Dashboard → Products:

**Free Plan:**
- Product: "CreatorPulse Free"
- Price: $0/month

**Pro Plan:**
- Product: "CreatorPulse Pro"
- Price: $19/month (recurring)
- Copy the Price ID (starts with `price_`)

**Agency Plan:**
- Product: "CreatorPulse Agency"
- Price: $99/month (recurring)
- Copy the Price ID (starts with `price_`)

### 4. Set Up Webhook
- Go to Stripe Dashboard → Developers → Webhooks
- Add endpoint: `https://your-project.supabase.co/functions/v1/stripe-webhook`
- Select events:
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
- Copy webhook secret (starts with `whsec_`)

### 5. Update Database
Run this SQL to add Stripe Price IDs to your plans:

```sql
UPDATE public.subscription_plans 
SET stripe_price_id_monthly = 'price_your_pro_price_id' 
WHERE id = 'pro';

UPDATE public.subscription_plans 
SET stripe_price_id_monthly = 'price_your_agency_price_id' 
WHERE id = 'agency';
```

## 🧪 Testing

### Test Cards (Stripe Test Mode)
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

### Test Flow
1. Start app: `streamlit run app/main.py`
2. Go to Billing page
3. Click "Subscribe to Pro"
4. Use test card: `4242 4242 4242 4242`
5. Complete checkout
6. Check subscription status in Billing page

## 🚀 Going Live

### 1. Switch to Live Keys
- Replace test keys with live keys in `.env`
- Update webhook endpoint to live URL
- Test with real payment methods

### 2. Business Verification
- Complete Stripe business verification
- Add bank account for payouts
- Set up tax information

### 3. Domain Verification
- Verify your domain in Stripe
- Update `RESEND_FROM` to your domain

## 📊 Monitoring

### Stripe Dashboard
- Monitor payments, subscriptions, and customers
- View analytics and reports
- Handle disputes and refunds

### CreatorPulse Analytics
- Track subscription conversions
- Monitor usage vs. limits
- Send usage alerts

## 🔒 Security Notes

- Never commit live keys to version control
- Use environment variables for all keys
- Enable webhook signature verification
- Monitor for suspicious activity
- Use HTTPS in production

## 💡 Tips

- Start with test mode for development
- Use Stripe CLI for local webhook testing
- Test all subscription scenarios
- Monitor webhook delivery
- Set up proper error handling
