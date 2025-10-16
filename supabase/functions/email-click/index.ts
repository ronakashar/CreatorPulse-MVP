import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    const user_id = url.searchParams.get('user')
    const draft_id = url.searchParams.get('draft')
    const target_url = url.searchParams.get('url')

    if (!target_url) {
      return new Response('Missing target URL', { status: 400, headers: corsHeaders })
    }

    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? '',
      {
        auth: {
          persistSession: false
        }
      }
    )

    // Insert click event
    const { error } = await supabaseClient
      .from('link_clicks')
      .insert({
        user_id: user_id || null,
        draft_id: draft_id ? parseInt(draft_id) : null,
        url: target_url,
        ua: req.headers.get('user-agent') || ''
      })

    if (error) {
      console.error('Error inserting click event:', error)
    }

    // Redirect to target URL
    return new Response(null, {
      status: 302,
      headers: {
        ...corsHeaders,
        'Location': target_url,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
    })
  } catch (error) {
    console.error('Error in email-click function:', error)
    return new Response('Error', { status: 500, headers: corsHeaders })
  }
})
