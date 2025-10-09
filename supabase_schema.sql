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
  source_value text
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

