import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { createClient } = await import('jsr:@supabase/supabase-js@2');
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: { persistSession: false }
    });

    // Get Stripe webhook secret
    const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET');
    if (!webhookSecret) {
      throw new Error('STRIPE_WEBHOOK_SECRET not set');
    }

    // Get request body and signature
    const body = await req.text();
    const signature = req.headers.get('stripe-signature');
    
    if (!signature) {
      throw new Error('No Stripe signature found');
    }

    // Verify webhook signature
    const stripe = await import('npm:stripe@14.21.0');
    const stripeClient = stripe.default(Deno.env.get('STRIPE_SECRET_KEY'));
    
    let event;
    try {
      event = stripeClient.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err) {
      console.error('Webhook signature verification failed:', err);
      return new Response('Webhook signature verification failed', { 
        status: 400,
        headers: corsHeaders 
      });
    }

    console.log('Processing webhook event:', event.type);

    // Handle different event types
    switch (event.type) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(supabase, event.data.object);
        break;
        
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
        await handleSubscriptionUpdated(supabase, event.data.object);
        break;
        
      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(supabase, event.data.object);
        break;
        
      case 'invoice.payment_succeeded':
        await handlePaymentSucceeded(supabase, event.data.object);
        break;
        
      case 'invoice.payment_failed':
        await handlePaymentFailed(supabase, event.data.object);
        break;
        
      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Webhook error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});

async function handleCheckoutCompleted(supabase: any, session: any) {
  console.log('Checkout completed:', session.id);
  
  // Get customer and subscription info
  const customerId = session.customer;
  const subscriptionId = session.subscription;
  
  if (!customerId || !subscriptionId) {
    console.error('Missing customer or subscription ID');
    return;
  }

  // Find user by email
  const { data: users, error } = await supabase
    .from('users')
    .select('id, email')
    .eq('email', session.customer_email)
    .limit(1);

  if (error || !users || users.length === 0) {
    console.error('User not found:', error);
    return;
  }

  const user = users[0];
  
  // Determine plan ID from price ID
  const priceId = session.line_items?.data?.[0]?.price?.id;
  let planId = 'pro'; // Default to pro plan
  
  // Map Stripe price IDs to plan IDs (you'll need to set these up in Stripe)
  if (priceId) {
    const { data: plans } = await supabase
      .from('subscription_plans')
      .select('id')
      .or(`stripe_price_id_monthly.eq.${priceId},stripe_price_id_yearly.eq.${priceId}`)
      .limit(1);
    
    if (plans && plans.length > 0) {
      planId = plans[0].id;
    }
  }

  // Create or update subscription
  const { error: subError } = await supabase
    .from('user_subscriptions')
    .upsert({
      user_id: user.id,
      plan_id: planId,
      stripe_customer_id: customerId,
      stripe_subscription_id: subscriptionId,
      status: 'active'
    });

  if (subError) {
    console.error('Failed to create subscription:', subError);
  } else {
    console.log('Subscription created successfully');
  }
}

async function handleSubscriptionUpdated(supabase: any, subscription: any) {
  console.log('Subscription updated:', subscription.id);
  
  const { error } = await supabase
    .from('user_subscriptions')
    .update({
      status: subscription.status,
      current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      trial_end: subscription.trial_end ? new Date(subscription.trial_end * 1000).toISOString() : null
    })
    .eq('stripe_subscription_id', subscription.id);

  if (error) {
    console.error('Failed to update subscription:', error);
  }
}

async function handleSubscriptionDeleted(supabase: any, subscription: any) {
  console.log('Subscription deleted:', subscription.id);
  
  const { error } = await supabase
    .from('user_subscriptions')
    .update({ status: 'canceled' })
    .eq('stripe_subscription_id', subscription.id);

  if (error) {
    console.error('Failed to cancel subscription:', error);
  }
}

async function handlePaymentSucceeded(supabase: any, invoice: any) {
  console.log('Payment succeeded:', invoice.id);
  // You can add additional logic here, like sending confirmation emails
}

async function handlePaymentFailed(supabase: any, invoice: any) {
  console.log('Payment failed:', invoice.id);
  // You can add additional logic here, like sending failure notifications
}
