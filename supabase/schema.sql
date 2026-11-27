-- Deník dobrodruha – Družina (Supabase)
-- Spusť celý soubor jednou v Supabase: SQL Editor → New query → vložit → Run.
-- Skript jde spustit i opakovaně (nic nesmaže).
--
-- Přihlášení: anonymní (Authentication → Sign In / Providers → Allow anonymous sign-ins = zapnuto).
-- Každé zařízení dostane neviditelný účet; hráč nic nevyplňuje.
--
-- Kdo co vidí (Row Level Security):
--   kampaň, členy a jejich veřejné údaje (jméno, povolání, úroveň, životy) – jen členové kampaně
--   celý deník postavy (member_sheets) – jen její hráč a PJ
--   skryté hody PJ – jen PJ (ostatní vidí řádek „skrytý hod“ bez výsledku přes pohled rolls_feed)
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

-- ---------------------------------------------------------------- pomocné funkce
create or replace function public.is_member(cid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from members where campaign_id = cid and user_id = auth.uid());
$$;

create or replace function public.is_gm(cid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from members where campaign_id = cid and user_id = auth.uid() and role = 'gm');
$$;

-- Založení kampaně: vygeneruje kód a zakladatele zapíše jako PJ.
create or replace function public.create_campaign(p_name text, p_system text, p_char_id text, p_snapshot jsonb)
returns public.campaigns
language plpgsql security definer set search_path = public as $$
declare
  alphabet constant text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  new_code text;
  camp campaigns;
begin
  if auth.uid() is null then raise exception 'Nejsi přihlášen.'; end if;
  loop
    new_code := '';
    for i in 1..6 loop
      new_code := new_code || substr(alphabet, 1 + floor(random() * length(alphabet))::int, 1);
      if i = 3 then new_code := new_code || '-'; end if;
    end loop;
    exit when not exists (select 1 from campaigns where code = new_code);
  end loop;
  insert into campaigns (name, system, code, gm) values (p_name, p_system, new_code, auth.uid()) returning * into camp;
  insert into members (campaign_id, user_id, role, char_id, snapshot)
    values (camp.id, auth.uid(), 'gm', p_char_id, coalesce(p_snapshot, '{}'::jsonb));
  return camp;
end $$;

-- Připojení kódem: kampaň musí být pro stejnou hru jako postava.
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
  insert into members (campaign_id, user_id, role, char_id, snapshot)
    values (camp.id, auth.uid(), 'player', p_char_id, coalesce(p_snapshot, '{}'::jsonb))
    on conflict (campaign_id, user_id) do update
      set char_id = excluded.char_id, snapshot = excluded.snapshot, last_seen = now();
  return camp;
end $$;

-- ---------------------------------------------------------------- pravidla přístupu
alter table public.campaigns     enable row level security;
alter table public.members       enable row level security;
alter table public.member_sheets enable row level security;
alter table public.rolls         enable row level security;
alter table public.shared_images enable row level security;

drop policy if exists "kampaň vidí členové" on public.campaigns;
create policy "kampaň vidí členové" on public.campaigns for select using (public.is_member(id));
drop policy if exists "kampaň mění PJ" on public.campaigns;
create policy "kampaň mění PJ" on public.campaigns for update using (gm = auth.uid()) with check (gm = auth.uid());
drop policy if exists "kampaň maže PJ" on public.campaigns;
create policy "kampaň maže PJ" on public.campaigns for delete using (gm = auth.uid());

drop policy if exists "členy vidí členové" on public.members;
create policy "členy vidí členové" on public.members for select using (public.is_member(campaign_id));
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
create policy "deník zapisuje hráč" on public.member_sheets for insert with check (user_id = auth.uid());
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

grant execute on function public.create_campaign(text, text, text, jsonb) to authenticated;
grant execute on function public.join_campaign(text, text, text, jsonb) to authenticated;
revoke execute on function public.create_campaign(text, text, text, jsonb) from anon;
revoke execute on function public.join_campaign(text, text, text, jsonb) from anon;

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
end $$;

-- ---------------------------------------------------------------- návrat ze schématu 2
-- Verze 0.13 (Stůl PJ, schvalování hráčů) je odložená. Pokud jsi spustil její skript, tento skript
-- vrátí server k fungování verze 0.12+: zakládání kampaně kódem a vstup bez schvalování.
-- Tabulka poznámek PJ ze schématu 2 zůstane prázdná a nevadí.
drop function if exists public.create_campaign(text, text);
do $$ begin
  update public.members set status = 'approved' where status <> 'approved';
exception when undefined_column then null; end $$;

-- ---------------------------------------------------------------- úpravy od PJ a tajné zprávy (0.16.1)
-- adjustments: PJ pošle hráči změnu životů, zkušeností nebo předmět; hráčova aplikace ji při
--              synchronizaci zapíše do deníku a označí jako použitou.
-- messages:    tajná zpráva PJ jednomu hráči (vidí jen adresát a PJ).

create table if not exists public.adjustments (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  user_id     uuid not null references auth.users (id) on delete cascade,   -- komu
  payload     jsonb not null,                                                -- životy, zkušenosti, předměty, důvod
  applied     boolean not null default false,
  created_at  timestamptz not null default now()
);
create index if not exists adjustments_target on public.adjustments (campaign_id, user_id, applied);

create table if not exists public.messages (
  id          bigint generated always as identity primary key,
  campaign_id uuid not null references public.campaigns (id) on delete cascade,
  to_user     uuid not null references auth.users (id) on delete cascade,
  body        text not null check (char_length(body) between 1 and 1000),
  created_at  timestamptz not null default now()
);

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

alter table public.adjustments enable row level security;
alter table public.messages    enable row level security;

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

grant select, insert, update, delete on public.adjustments to authenticated;
grant select, insert on public.messages to authenticated;
