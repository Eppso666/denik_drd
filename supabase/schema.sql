-- Deník dobrodruha – Družina na vlastním serveru PJ (Supabase), verze schématu 2
-- Spusť celý soubor v Supabase: SQL Editor → New query → vložit → Run.
-- Skript jde spustit i opakovaně a přes verzi 1 (nic nesmaže, jen doplní).
--
-- Přihlášení: anonymní (Authentication → Sign In / Providers → Allow anonymous sign-ins = zapnuto).
-- Každé zařízení dostane neviditelný účet; hráč nic nevyplňuje.
--
-- Pán jeskyně = vlastník serveru. Při nastavení v aplikaci se server „zamkne“ klíčem PJ
-- (claim_server). Kampaně smí zakládat jen PJ; stejným klíčem se PJ přihlásí i na dalším zařízení.
--
-- Kdo co vidí (Row Level Security):
--   kampaň, členy a jejich veřejné údaje – jen přijatí členové kampaně (čekající hráč vidí jen sebe a název)
--   celý deník postavy (member_sheets) – jen její hráč a PJ
--   skryté hody PJ – jen PJ (ostatní vidí „skrytý hod“ bez výsledku přes pohled rolls_feed)
--   úpravy od PJ (životy, zkušenosti, předměty) a tajné zprávy – jen PJ a hráč, kterému patří
--   poznámky PJ – jen PJ
--   obrázky – vidí členové, nahrává jen PJ

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- tabulky
create table if not exists public.campaigns (
  id          uuid primary key default gen_random_uuid(),
  name        text not null check (char_length(name) between 1 and 80),
  system      text not null check (system in ('dh', 'drd')),
  code        text not null unique check (code ~ '^[A-Z2-9]{3}-[A-Z2-9]{3}$'),
  session     int  not null default 1 check (session >= 1),
  gm          uuid not null references auth.users (id) on delete cascade,
  created_at  timestamptz not null default now()
);
alter table public.campaigns add column if not exists locked boolean not null default false;

create table if not exists public.members (
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  user_id     uuid not null references auth.users (id) on delete cascade,
  role        text not null check (role in ('gm', 'player')),
  char_id     text,
  snapshot    jsonb not null default '{}'::jsonb,   -- jméno, rasa, povolání, úroveň, životy
  share_rolls boolean not null default true,
  share_hp    boolean not null default true,
  last_seen   timestamptz not null default now(),
  primary key (campaign_id, user_id)
);
alter table public.members add column if not exists status text not null default 'approved';
do $$ begin
  alter table public.members add constraint members_status_check check (status in ('pending', 'approved'));
exception when duplicate_object then null; end $$;

create table if not exists public.member_sheets (
  campaign_id uuid not null,
  user_id     uuid not null,
  sheet       jsonb not null default '{}'::jsonb,   -- celý deník postavy (kopie)
  updated_at  timestamptz not null default now(),
  primary key (campaign_id, user_id),
  foreign key (campaign_id, user_id) references public.members (campaign_id, user_id) on delete cascade
);

create table if not exists public.rolls (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
  who         text not null check (char_length(who) <= 80),
  label       text not null check (char_length(label) <= 120),
  result      text not null check (char_length(result) <= 40),
  detail      text not null default '' check (char_length(detail) <= 300),
  hidden      boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists rolls_campaign_time on public.rolls (campaign_id, created_at desc);

create table if not exists public.shared_images (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
  title       text not null check (char_length(title) <= 120),
  path        text not null,                          -- cesta v úložišti campaign-images
  created_at  timestamptz not null default now()
);

-- Úpravy postavy od PJ: hráčova aplikace je při synchronizaci použije a označí jako použité.
create table if not exists public.adjustments (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  user_id     uuid not null references auth.users (id) on delete cascade,   -- komu
  payload     jsonb not null,                                                -- životy, zkušenosti, předměty, důvod
  applied     boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists adjustments_target on public.adjustments (campaign_id, user_id, applied);

-- Tajné zprávy PJ jednomu hráči.
create table if not exists public.messages (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  to_user     uuid not null references auth.users (id) on delete cascade,
  body        text not null check (char_length(body) between 1 and 1000),
  created_at  timestamptz not null default now()
);

-- Poznámky PJ ke kampani (tajné).
create table if not exists public.gm_notes (
  campaign_id uuid primary key references public.campaigns (id) on delete cascade,
  notes       jsonb not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);

-- Vlastník serveru: otisk klíče PJ a seznam zařízení přihlášených jako PJ.
create table if not exists public.server_owner (
  id          int primary key default 1 check (id = 1),
  key_hash    text not null,
  created_at  timestamptz not null default now()
);
create table if not exists public.server_admins (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  created_at  timestamptz not null default now()
);

-- ---------------------------------------------------------------- pomocné funkce
create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from server_admins where user_id = auth.uid());
$$;

-- přijatý člen kampaně (PJ serveru vidí všechny své kampaně)
create or replace function public.is_member(cid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select public.is_admin()
      or exists (select 1 from members where campaign_id = cid and user_id = auth.uid() and status = 'approved');
$$;

-- člen v jakémkoli stavu (i čekající na schválení)
create or replace function public.is_joined(cid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from members where campaign_id = cid and user_id = auth.uid());
$$;

create or replace function public.is_gm(cid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select public.is_admin()
      or exists (select 1 from members where campaign_id = cid and user_id = auth.uid() and role = 'gm');
$$;

-- Stav serveru pro průvodce v aplikaci (smí volat i nepřihlášený).
create or replace function public.denik_info() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('version', 2, 'owned', exists (select 1 from server_owner),
                            'admin', public.is_admin());
$$;

-- První volání server zamkne klíčem PJ; další zařízení se stejným klíčem se stanou PJ.
create or replace function public.claim_server(p_key text) returns boolean
language plpgsql security definer set search_path = public, extensions as $$
declare h text;
begin
  if auth.uid() is null then raise exception 'Nejsi přihlášen.'; end if;
  if char_length(coalesce(p_key, '')) < 12 then raise exception 'Klíč PJ je příliš krátký.'; end if;
  h := encode(digest(p_key, 'sha256'), 'hex');
  lock table server_owner in exclusive mode;
  if not exists (select 1 from server_owner) then
    insert into server_owner (id, key_hash) values (1, h);
  elsif not exists (select 1 from server_owner where key_hash = h) then
    return false;
  end if;
  insert into server_admins (user_id) values (auth.uid()) on conflict do nothing;
  return true;
end $$;

-- Založení kampaně (jen PJ serveru): vygeneruje kód a zakladatele zapíše jako PJ.
drop function if exists public.create_campaign(text, text, text, jsonb);
create or replace function public.create_campaign(p_name text, p_system text)
returns public.campaigns
language plpgsql security definer set search_path = public as $$
declare
  alphabet constant text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  new_code text;
  camp campaigns;
begin
  if auth.uid() is null then raise exception 'Nejsi přihlášen.'; end if;
  if not public.is_admin() then raise exception 'Kampaň na tomto serveru zakládá jen jeho PJ.'; end if;
  loop
    new_code := '';
    for i in 1..6 loop
      new_code := new_code || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1);
      if i = 3 then new_code := new_code || '-'; end if;
    end loop;
    exit when not exists (select 1 from campaigns where code = new_code);
  end loop;
  insert into campaigns (name, system, code, gm) values (p_name, p_system, new_code, auth.uid()) returning * into camp;
  insert into members (campaign_id, user_id, role, snapshot, status)
    values (camp.id, auth.uid(), 'gm', jsonb_build_object('name', 'Pán jeskyně'), 'approved');
  return camp;
end $$;

-- Žádost o vstup kódem: kampaň musí být pro stejnou hru jako postava a nesmí být zamčená.
-- Hráč čeká, dokud ho PJ nepřijme.
create or replace function public.join_campaign(p_code text, p_system text, p_char_id text, p_snapshot jsonb)
returns public.campaigns
language plpgsql security definer set search_path = public as $$
declare camp campaigns;
begin
  if auth.uid() is null then raise exception 'Nejsi přihlášen.'; end if;
  select * into camp from campaigns where code = upper(p_code);
  if not found then raise exception 'Kampaň s tímto kódem neexistuje.'; end if;
  if camp.system <> p_system then
    raise exception 'Kampaň je pro jinou hru – připoj se postavou pro %.',
      case camp.system when 'dh' then 'Dračí Hlídku' else 'Dračí doupě 1.6' end;
  end if;
  if camp.locked and not public.is_joined(camp.id) then
    raise exception 'Kampaň je zamčená – PJ nové hráče nepřijímá.';
  end if;
  insert into members (campaign_id, user_id, role, char_id, snapshot, status)
    values (camp.id, auth.uid(), 'player', p_char_id, coalesce(p_snapshot, '{}'::jsonb), 'pending')
    on conflict (campaign_id, user_id) do update
      set char_id = excluded.char_id, snapshot = excluded.snapshot, last_seen = now();
  return camp;
end $$;

-- Hráč si nesmí sám změnit roli ani se přijmout.
create or replace function public.members_guard() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_gm(old.campaign_id) then
    new.role := old.role;
    new.status := old.status;
  end if;
  new.campaign_id := old.campaign_id;
  new.user_id := old.user_id;
  return new;
end $$;
drop trigger if exists members_guard on public.members;
create trigger members_guard before update on public.members for each row execute function public.members_guard();

-- Hráč u úpravy od PJ smí změnit jen „použito“.
create or replace function public.adjustments_guard() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if not public.is_gm(old.campaign_id) then
    new.payload := old.payload;
    new.user_id := old.user_id;
    new.campaign_id := old.campaign_id;
  end if;
  return new;
end $$;
drop trigger if exists adjustments_guard on public.adjustments;
create trigger adjustments_guard before update on public.adjustments for each row execute function public.adjustments_guard();

-- ---------------------------------------------------------------- pravidla přístupu
alter table public.campaigns     enable row level security;
alter table public.members       enable row level security;
alter table public.member_sheets enable row level security;
alter table public.rolls         enable row level security;
alter table public.shared_images enable row level security;
alter table public.adjustments   enable row level security;
alter table public.messages      enable row level security;
alter table public.gm_notes      enable row level security;
alter table public.server_owner  enable row level security;   -- bez pravidel: nikdo zvenku
alter table public.server_admins enable row level security;

drop policy if exists "kampaň vidí členové" on public.campaigns;
create policy "kampaň vidí členové" on public.campaigns for select using (public.is_member(id) or public.is_joined(id));
drop policy if exists "kampaň mění PJ" on public.campaigns;
create policy "kampaň mění PJ" on public.campaigns for update using (public.is_gm(id)) with check (public.is_gm(id));
drop policy if exists "kampaň maže PJ" on public.campaigns;
create policy "kampaň maže PJ" on public.campaigns for delete using (public.is_gm(id));

drop policy if exists "členy vidí členové" on public.members;
create policy "členy vidí členové" on public.members for select
  using (public.is_member(campaign_id) or user_id = auth.uid());
drop policy if exists "svůj řádek mění hráč, cizí PJ" on public.members;
create policy "svůj řádek mění hráč, cizí PJ" on public.members for update
  using (user_id = auth.uid() or public.is_gm(campaign_id))
  with check (user_id = auth.uid() or public.is_gm(campaign_id));
drop policy if exists "odchod nebo vyloučení" on public.members;
create policy "odchod nebo vyloučení" on public.members for delete
  using (user_id = auth.uid() or public.is_gm(campaign_id));

drop policy if exists "deník vidí hráč a PJ" on public.member_sheets;
create policy "deník vidí hráč a PJ" on public.member_sheets for select
  using (user_id = auth.uid() or public.is_gm(campaign_id));
drop policy if exists "deník zapisuje hráč" on public.member_sheets;
create policy "deník zapisuje hráč" on public.member_sheets for insert
  with check (user_id = auth.uid() and public.is_member(campaign_id));
drop policy if exists "deník mění hráč" on public.member_sheets;
create policy "deník mění hráč" on public.member_sheets for update
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "hody vidí členové" on public.rolls;
create policy "hody vidí členové" on public.rolls for select
  using (public.is_member(campaign_id) and (not hidden or user_id = auth.uid() or public.is_gm(campaign_id)));
drop policy if exists "hází člen" on public.rolls;
create policy "hází člen" on public.rolls for insert
  with check (user_id = auth.uid() and public.is_member(campaign_id) and (not hidden or public.is_gm(campaign_id)));

drop policy if exists "obrázky vidí členové" on public.shared_images;
create policy "obrázky vidí členové" on public.shared_images for select using (public.is_member(campaign_id));
drop policy if exists "obrázky sdílí PJ" on public.shared_images;
create policy "obrázky sdílí PJ" on public.shared_images for insert
  with check (user_id = auth.uid() and public.is_gm(campaign_id));
drop policy if exists "obrázky maže PJ" on public.shared_images;
create policy "obrázky maže PJ" on public.shared_images for delete using (public.is_gm(campaign_id));

drop policy if exists "úpravy vidí PJ a hráč" on public.adjustments;
create policy "úpravy vidí PJ a hráč" on public.adjustments for select
  using (user_id = auth.uid() or public.is_gm(campaign_id));
drop policy if exists "úpravy dělá PJ" on public.adjustments;
create policy "úpravy dělá PJ" on public.adjustments for insert with check (public.is_gm(campaign_id));
drop policy if exists "úpravu potvrdí hráč" on public.adjustments;
create policy "úpravu potvrdí hráč" on public.adjustments for update
  using (user_id = auth.uid() or public.is_gm(campaign_id))
  with check (user_id = auth.uid() or public.is_gm(campaign_id));
drop policy if exists "úpravy maže PJ" on public.adjustments;
create policy "úpravy maže PJ" on public.adjustments for delete using (public.is_gm(campaign_id));

drop policy if exists "zprávy čte adresát a PJ" on public.messages;
create policy "zprávy čte adresát a PJ" on public.messages for select
  using (to_user = auth.uid() or public.is_gm(campaign_id));
drop policy if exists "zprávy posílá PJ" on public.messages;
create policy "zprávy posílá PJ" on public.messages for insert with check (public.is_gm(campaign_id));

drop policy if exists "poznámky jen PJ" on public.gm_notes;
create policy "poznámky jen PJ" on public.gm_notes for all
  using (public.is_gm(campaign_id)) with check (public.is_gm(campaign_id));

drop policy if exists "PJ vidí sebe" on public.server_admins;
create policy "PJ vidí sebe" on public.server_admins for select using (user_id = auth.uid());

-- Skryté hody ostatní hráči vidí jen jako „skrytý hod“ (bez výsledku).
create or replace view public.rolls_feed with (security_invoker = false) as
  select r.id, r.campaign_id, r.who,
         case when r.hidden and r.user_id <> auth.uid() and not public.is_gm(r.campaign_id)
              then 'Skrytý hod' else r.label end as label,
         case when r.hidden and r.user_id <> auth.uid() and not public.is_gm(r.campaign_id)
              then 'jen pro PJ' else r.result end as result,
         case when r.hidden and r.user_id <> auth.uid() and not public.is_gm(r.campaign_id)
              then '' else r.detail end as detail,
         r.hidden, r.created_at
  from public.rolls r
  where public.is_member(r.campaign_id);
grant select on public.rolls_feed to authenticated;

grant execute on function public.create_campaign(text, text) to authenticated;
grant execute on function public.join_campaign(text, text, text, jsonb) to authenticated;
grant execute on function public.claim_server(text) to authenticated;
grant execute on function public.denik_info() to anon, authenticated;
revoke execute on function public.create_campaign(text, text) from anon;
revoke execute on function public.join_campaign(text, text, text, jsonb) from anon;
revoke execute on function public.claim_server(text) from anon;

-- ---------------------------------------------------------------- úložiště obrázků
insert into storage.buckets (id, name, public) values ('campaign-images', 'campaign-images', false)
  on conflict (id) do nothing;

drop policy if exists "obrázky kampaně čtou členové" on storage.objects;
create policy "obrázky kampaně čtou členové" on storage.objects for select
  using (bucket_id = 'campaign-images' and public.is_member(((storage.foldername(name))[1])::uuid));
drop policy if exists "obrázky kampaně nahrává PJ" on storage.objects;
create policy "obrázky kampaně nahrává PJ" on storage.objects for insert
  with check (bucket_id = 'campaign-images' and public.is_gm(((storage.foldername(name))[1])::uuid));
drop policy if exists "obrázky kampaně maže PJ" on storage.objects;
create policy "obrázky kampaně maže PJ" on storage.objects for delete
  using (bucket_id = 'campaign-images' and public.is_gm(((storage.foldername(name))[1])::uuid));

-- ---------------------------------------------------------------- živé změny (Realtime)
do $$ begin
  begin alter publication supabase_realtime add table public.rolls; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.members; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.shared_images; exception when duplicate_object then null; end;
exception when undefined_object then null; end $$;
