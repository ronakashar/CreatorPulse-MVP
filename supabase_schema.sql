-- Users
create table if not exists public.users (
  id uuid primary key,
  email text unique,
  name text,
  timezone text
);

-- Sources
create table if not exists public.user_sources (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  source_type text check (source_type in ('twitter','youtube','rss')),
  source_value text,
  boost_factor real default 1.0 check (boost_factor >= 0.1 and boost_factor <= 3.0)
);
create index if not exists idx_user_sources_user_type on public.user_sources(user_id, source_type);

-- Content items
create table if not exists public.content_items (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  source_id bigint references public.user_sources(id) on delete set null,
  title text,
  url text,
  summary text,
  created_at timestamptz default now()
);
create unique index if not exists uniq_content_by_user_url on public.content_items(user_id, url);
create index if not exists idx_content_user_created on public.content_items(user_id, created_at desc);

-- Drafts
create table if not exists public.drafts (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  draft_text text,
  feedback text,
  sent boolean default false,
  created_at timestamptz default now()
);
create index if not exists idx_drafts_user_created on public.drafts(user_id, created_at desc);

-- Storage bucket note (create in dashboard): style-samples

-- Delivery preferences (Milestone 1)
alter table if exists public.users
  add column if not exists send_time_local text,
  add column if not exists send_days text[],
  add column if not exists frequency text check (frequency in ('daily','weekly')) default 'daily';

-- Milestone 3: track edited drafts and diffs
create table if not exists public.draft_edits (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  original_draft_id bigint references public.drafts(id) on delete set null,
  original_text text,
  edited_text text,
  diff_text text,
  created_at timestamptz default now()
);

-- Milestone 5: Add boost factor to existing sources
alter table if exists public.user_sources 
  add column if not exists boost_factor real default 1.0 check (boost_factor >= 0.1 and boost_factor <= 3.0);
create index if not exists idx_draft_edits_user_created on public.draft_edits(user_id, created_at desc);

-- Milestone 6: Workspaces & Roles
create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text unique not null,
  description text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.workspace_members (
  id bigserial primary key,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  user_id uuid references public.users(id) on delete cascade,
  role text check (role in ('owner','admin','editor','viewer')) default 'viewer',
  invited_at timestamptz default now(),
  joined_at timestamptz,
  invited_by uuid references public.users(id),
  unique(workspace_id, user_id)
);

-- Add workspace_id to existing tables
alter table if exists public.user_sources 
  add column if not exists workspace_id uuid references public.workspaces(id) on delete cascade;

alter table if exists public.content_items 
  add column if not exists workspace_id uuid references public.workspaces(id) on delete cascade;

alter table if exists public.drafts 
  add column if not exists workspace_id uuid references public.workspaces(id) on delete cascade;

alter table if exists public.draft_edits 
  add column if not exists workspace_id uuid references public.workspaces(id) on delete cascade;

-- Indexes for workspace queries
create index if not exists idx_workspace_members_workspace on public.workspace_members(workspace_id);
create index if not exists idx_workspace_members_user on public.workspace_members(user_id);
create index if not exists idx_user_sources_workspace on public.user_sources(workspace_id);
create index if not exists idx_content_items_workspace on public.content_items(workspace_id);
create index if not exists idx_drafts_workspace on public.drafts(workspace_id);
-- Milestone 6: Stripe Integration & Billing
create table if not exists public.subscription_plans (
  id text primary key,
  name text not null,
  description text,
  price_monthly_cents integer not null,
  price_yearly_cents integer,
  features jsonb not null default '{}',
  limits jsonb not null default '{}',
  stripe_price_id_monthly text,
  stripe_price_id_yearly text,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists public.user_subscriptions (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  plan_id text references public.subscription_plans(id),
  stripe_subscription_id text unique,
  stripe_customer_id text,
  status text check (status in ('active','canceled','past_due','unpaid','trialing')) default 'active',
  current_period_start timestamptz,
  current_period_end timestamptz,
  trial_end timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.usage_tracking (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  metric_type text not null check (metric_type in ('newsletter_sent','api_call','storage_mb','source_fetch')),
  metric_value numeric not null default 1,
  metadata jsonb,
  created_at timestamptz default now()
);

-- Indexes for billing queries
create index if not exists idx_user_subscriptions_user on public.user_subscriptions(user_id);
create index if not exists idx_user_subscriptions_stripe on public.user_subscriptions(stripe_subscription_id);
create index if not exists idx_usage_tracking_user_date on public.usage_tracking(user_id, created_at desc);
create index if not exists idx_usage_tracking_workspace_date on public.usage_tracking(workspace_id, created_at desc);

-- Insert default subscription plans
insert into public.subscription_plans (id, name, description, price_monthly_cents, price_yearly_cents, features, limits) values
('free', 'Free', 'Perfect for getting started', 0, 0, 
 '{"workspaces": 1, "team_members": 1, "sources": 5, "newsletters_per_month": 10, "analytics": false, "priority_support": false}',
 '{"max_workspaces": 1, "max_team_members": 1, "max_sources": 5, "max_newsletters_per_month": 10}'),
('pro', 'Pro', 'For serious creators and small teams', 1900, 19000,
 '{"workspaces": 5, "team_members": 10, "sources": 50, "newsletters_per_month": 100, "analytics": true, "priority_support": true}',
 '{"max_workspaces": 5, "max_team_members": 10, "max_sources": 50, "max_newsletters_per_month": 100}'),
('agency', 'Agency', 'For agencies managing multiple clients', 9900, 99000,
 '{"workspaces": 50, "team_members": 100, "sources": 500, "newsletters_per_month": 1000, "analytics": true, "priority_support": true, "white_label": true}',
 '{"max_workspaces": 50, "max_team_members": 100, "max_sources": 500, "max_newsletters_per_month": 1000}')
-- Milestone 6: Agency Dashboard & Client Management
create table if not exists public.client_profiles (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid references public.workspaces(id) on delete cascade,
  client_name text not null,
  client_email text,
  client_website text,
  industry text,
  contact_person text,
  notes text,
  branding jsonb default '{}',
  settings jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.client_workspaces (
  id uuid primary key default gen_random_uuid(),
  agency_workspace_id uuid references public.workspaces(id) on delete cascade,
  client_profile_id uuid references public.client_profiles(id) on delete cascade,
  client_workspace_id uuid references public.workspaces(id) on delete cascade,
  created_at timestamptz default now(),
  unique(agency_workspace_id, client_profile_id)
);

create table if not exists public.bulk_operations (
  id bigserial primary key,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  operation_type text not null check (operation_type in ('newsletter_send','source_fetch','draft_generate')),
  target_workspaces jsonb not null default '[]',
  status text check (status in ('pending','running','completed','failed')) default 'pending',
  progress jsonb default '{}',
  results jsonb default '{}',
  error_message text,
  created_by uuid references public.users(id),
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now()
);

-- Indexes for agency queries
create index if not exists idx_client_profiles_workspace on public.client_profiles(workspace_id);
create index if not exists idx_client_workspaces_agency on public.client_workspaces(agency_workspace_id);
create index if not exists idx_client_workspaces_client on public.client_workspaces(client_workspace_id);
create index if not exists idx_bulk_operations_workspace on public.bulk_operations(workspace_id);
-- Milestone 6: Enhanced Usage Analytics
create table if not exists public.analytics_events (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  event_type text not null check (event_type in ('api_call','storage_upload','email_sent','source_fetch','draft_generate','user_action')),
  event_category text not null,
  event_name text not null,
  metadata jsonb default '{}',
  cost_cents integer default 0,
  created_at timestamptz default now()
);

create table if not exists public.analytics_reports (
  id bigserial primary key,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  report_type text not null check (report_type in ('usage','performance','cost','engagement')),
  period_start timestamptz not null,
  period_end timestamptz not null,
  data jsonb not null default '{}',
  generated_at timestamptz default now(),
  generated_by uuid references public.users(id)
);

create table if not exists public.analytics_dashboards (
  id bigserial primary key,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  dashboard_name text not null,
  dashboard_config jsonb not null default '{}',
  is_default boolean default false,
  created_by uuid references public.users(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Indexes for analytics queries
create index if not exists idx_analytics_events_user_date on public.analytics_events(user_id, created_at desc);
create index if not exists idx_analytics_events_workspace_date on public.analytics_events(workspace_id, created_at desc);
create index if not exists idx_analytics_events_type_date on public.analytics_events(event_type, created_at desc);
create index if not exists idx_analytics_reports_workspace on public.analytics_reports(workspace_id);
create index if not exists idx_analytics_dashboards_workspace on public.analytics_dashboards(workspace_id);

-- Milestone 4: analytics tables
create table if not exists public.email_events (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  draft_id bigint references public.drafts(id) on delete set null,
  event_type text check (event_type in ('open','click')),
  meta jsonb,
  created_at timestamptz default now()
);
create index if not exists idx_email_events_user_created on public.email_events(user_id, created_at desc);

create table if not exists public.link_clicks (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  draft_id bigint references public.drafts(id) on delete set null,
  url text,
  ua text,
  created_at timestamptz default now()
);
create index if not exists idx_link_clicks_user_created on public.link_clicks(user_id, created_at desc);

-- Permissive RLS for MVP: allow anon insert for tracking
alter table public.email_events enable row level security;
alter table public.link_clicks enable row level security;
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='email_events' and policyname='allow_insert_email_events') then
    create policy "allow_insert_email_events" on public.email_events for insert to anon with check (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='link_clicks' and policyname='allow_insert_link_clicks') then
    create policy "allow_insert_link_clicks" on public.link_clicks for insert to anon with check (true);
  end if;
end $$;

