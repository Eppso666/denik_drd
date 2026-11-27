-- Deník dobrodruha – úpravy od PJ a tajné zprávy (verze 0.16.1)
-- Spusť jednou v Supabase: SQL Editor → New query → vložit celý soubor → Run.
-- Jde spustit i opakovaně a nic nesmaže. Je to také konec souboru schema.sql.
--
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
