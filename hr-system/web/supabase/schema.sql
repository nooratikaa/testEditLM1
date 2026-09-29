-- Meja HR — skema pangkalan data Supabase
-- Jalankan SEKALI dalam Supabase: SQL Editor → New query → tampal fail ini → Run.
--
-- Keselamatan dikuatkuasakan oleh pangkalan data (Row Level Security):
--   staf  : hanya boleh membaca rekod sendiri dan memohon / membatalkan cuti sendiri
--   boss  : boleh membaca semua rekod dan meluluskan / menolak cuti
--   hr    : boleh membaca dan mengubah semua rekod

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- tables
create table if not exists public.employees (
  id              text primary key default gen_random_uuid()::text,
  staff_no        text not null unique,
  role            text not null default 'staff' check (role in ('staff', 'hr', 'boss')),
  user_id         uuid unique references auth.users (id) on delete set null,
  login_email     text,
  activation_code text,
  data            jsonb not null default '{}'::jsonb,
  updated_at      timestamptz not null default now()
);

create table if not exists public.positions (
  id   text primary key default gen_random_uuid()::text,
  data jsonb not null default '{}'::jsonb
);

create table if not exists public.leaves (
  id         text primary key default gen_random_uuid()::text,
  emp_id     text not null references public.employees (id) on delete cascade,
  data       jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.targets (
  id     text primary key,            -- '<yyyy-mm>_<emp_id>'
  emp_id text not null references public.employees (id) on delete cascade,
  month  text not null,
  data   jsonb not null default '{}'::jsonb
);

create table if not exists public.attendance (
  id     text primary key,            -- '<yyyy-mm>_<emp_id>'
  emp_id text not null references public.employees (id) on delete cascade,
  month  text not null,
  data   jsonb not null default '{}'::jsonb   -- { "marks": { "07": "TH", "12": "H2", ... } }
);

create table if not exists public.warnings (
  id     text primary key default gen_random_uuid()::text,
  emp_id text not null references public.employees (id) on delete cascade,
  data   jsonb not null default '{}'::jsonb
);

create table if not exists public.settings (
  id   int primary key default 1 check (id = 1),
  data jsonb not null default '{}'::jsonb
);
insert into public.settings (id, data) values (1, '{}'::jsonb) on conflict (id) do nothing;

create index if not exists leaves_emp_idx on public.leaves (emp_id);
create index if not exists targets_emp_idx on public.targets (emp_id);
create index if not exists attendance_emp_idx on public.attendance (emp_id);
create index if not exists warnings_emp_idx on public.warnings (emp_id);

-- ---------------------------------------------------------------- who is calling
create or replace function public.my_emp_id() returns text
language sql stable security definer set search_path = public as $$
  select id from public.employees where user_id = auth.uid()
$$;

create or replace function public.my_role() returns text
language sql stable security definer set search_path = public as $$
  select role from public.employees where user_id = auth.uid()
$$;

create or replace function public.is_hr() returns boolean
language sql stable as $$ select coalesce(public.my_role() = 'hr', false) $$;

create or replace function public.is_manager() returns boolean
language sql stable as $$ select coalesce(public.my_role() in ('hr', 'boss'), false) $$;

-- ---------------------------------------------------------------- row level security
alter table public.employees  enable row level security;
alter table public.positions  enable row level security;
alter table public.leaves     enable row level security;
alter table public.targets    enable row level security;
alter table public.attendance enable row level security;
alter table public.warnings   enable row level security;
alter table public.settings   enable row level security;

-- employees: own row, or everything for HR/boss; only HR writes
drop policy if exists emp_read on public.employees;
create policy emp_read on public.employees for select to authenticated
  using (user_id = auth.uid() or public.is_manager());
drop policy if exists emp_write on public.employees;
create policy emp_write on public.employees for all to authenticated
  using (public.is_hr()) with check (public.is_hr());

-- positions & settings: every signed-in person reads; only HR writes
drop policy if exists pos_read on public.positions;
create policy pos_read on public.positions for select to authenticated using (public.my_emp_id() is not null);
drop policy if exists pos_write on public.positions;
create policy pos_write on public.positions for all to authenticated using (public.is_hr()) with check (public.is_hr());
drop policy if exists set_read on public.settings;
create policy set_read on public.settings for select to authenticated using (public.my_emp_id() is not null);
drop policy if exists set_write on public.settings;
create policy set_write on public.settings for update to authenticated using (public.is_hr()) with check (public.is_hr());

-- leaves: staff read their own, apply for themselves, and change/cancel only while pending
drop policy if exists leave_read on public.leaves;
create policy leave_read on public.leaves for select to authenticated
  using (emp_id = public.my_emp_id() or public.is_manager());
drop policy if exists leave_insert on public.leaves;
create policy leave_insert on public.leaves for insert to authenticated
  with check (public.is_hr() or emp_id = public.my_emp_id());
drop policy if exists leave_update on public.leaves;
create policy leave_update on public.leaves for update to authenticated
  using (public.is_manager() or (emp_id = public.my_emp_id() and data->>'status' = 'Menunggu'))
  with check (public.is_manager() or (emp_id = public.my_emp_id() and data->>'status' = 'Menunggu'));
drop policy if exists leave_delete on public.leaves;
create policy leave_delete on public.leaves for delete to authenticated
  using (public.is_hr() or (emp_id = public.my_emp_id() and data->>'status' = 'Menunggu'));

-- targets, attendance, warnings: staff read their own; HR/boss read all; only HR writes
drop policy if exists tgt_read on public.targets;
create policy tgt_read on public.targets for select to authenticated using (emp_id = public.my_emp_id() or public.is_manager());
drop policy if exists tgt_write on public.targets;
create policy tgt_write on public.targets for all to authenticated using (public.is_hr()) with check (public.is_hr());

drop policy if exists att_read on public.attendance;
create policy att_read on public.attendance for select to authenticated using (emp_id = public.my_emp_id() or public.is_manager());
drop policy if exists att_write on public.attendance;
create policy att_write on public.attendance for all to authenticated using (public.is_hr()) with check (public.is_hr());

drop policy if exists warn_read on public.warnings;
create policy warn_read on public.warnings for select to authenticated using (emp_id = public.my_emp_id() or public.is_manager());
drop policy if exists warn_write on public.warnings;
create policy warn_write on public.warnings for all to authenticated using (public.is_hr()) with check (public.is_hr());

-- ---------------------------------------------------------------- leave integrity
-- Days are counted on the server from the company's workdays and public holidays,
-- and a staff member can never approve their own leave.
create or replace function public.count_leave_days(p_from date, p_to date, p_half boolean)
returns numeric language plpgsql stable security definer set search_path = public as $$
declare
  s jsonb := coalesce((select data from public.settings where id = 1), '{}'::jsonb);
  wd jsonb := coalesce(s->'workdays', '[1,2,3,4,5]'::jsonb);
  hol jsonb := coalesce(s->'holidays', '[]'::jsonb);
  d date; n numeric := 0;
begin
  if p_from is null or p_to is null or p_to < p_from then return 0; end if;
  d := p_from;
  while d <= p_to loop
    if wd @> to_jsonb(extract(dow from d)::int)
       and not exists (select 1 from jsonb_array_elements(hol) h where h->>'date' = to_char(d, 'YYYY-MM-DD')) then
      n := n + 1;
    end if;
    d := d + 1;
  end loop;
  if p_half and p_from = p_to and n > 0 then n := 0.5; end if;
  return n;
end $$;

create or replace function public.leaves_guard() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  new.data := new.data || jsonb_build_object(
    'empId', new.emp_id,
    'days', public.count_leave_days((new.data->>'from')::date, (new.data->>'to')::date, coalesce((new.data->>'half')::boolean, false)));
  if not public.is_manager() then
    new.data := (new.data - 'decidedAt' - 'decidedBy') || jsonb_build_object('status', 'Menunggu');
  end if;
  if tg_op = 'INSERT' then
    new.data := new.data || jsonb_build_object('createdAt', to_char(now() at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'));
  else
    new.data := new.data || jsonb_build_object('createdAt', old.data->'createdAt');
    new.emp_id := old.emp_id;
    new.data := new.data || jsonb_build_object('empId', old.emp_id);
  end if;
  if (new.data->>'days')::numeric <= 0 then
    raise exception 'Tempoh cuti tiada hari bekerja';
  end if;
  return new;
end $$;
drop trigger if exists leaves_guard on public.leaves;
create trigger leaves_guard before insert or update on public.leaves
  for each row execute function public.leaves_guard();

-- ---------------------------------------------------------------- staff login
-- Staff sign in with their staff number. HR gives each person a one-time activation code;
-- the first sign-up must carry a valid staff number + code or it is refused.
create or replace function public.login_email(p_staff_no text) returns text
language sql stable security definer set search_path = public as $$
  select login_email from public.employees where upper(staff_no) = upper(trim(p_staff_no)) and user_id is not null
$$;
revoke all on function public.login_email(text) from public;
grant execute on function public.login_email(text) to anon, authenticated;

create or replace function public.claim_staff_account() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  v_no text := upper(trim(coalesce(new.raw_user_meta_data->>'staff_no', '')));
  v_code text := upper(trim(coalesce(new.raw_user_meta_data->>'code', '')));
  v_id text;
begin
  update public.employees
     set user_id = new.id, login_email = new.email, activation_code = null, updated_at = now()
   where upper(staff_no) = v_no and upper(activation_code) = v_code and v_code <> '' and user_id is null
   returning id into v_id;
  if v_id is null then
    raise exception 'No. staf atau kod aktivasi tidak sah';
  end if;
  return new;
end $$;
drop trigger if exists claim_staff_account on auth.users;
create trigger claim_staff_account after insert on auth.users
  for each row execute function public.claim_staff_account();

-- ---------------------------------------------------------------- first HR account
-- Creates the first HR record (staff no. HR001) with a random activation code and shows it.
insert into public.employees (staff_no, role, activation_code, data)
select 'HR001', 'hr', upper(substr(md5(gen_random_uuid()::text), 1, 6)),
       jsonb_build_object('name', 'Pentadbir HR', 'status', 'Aktif', 'joinDate', to_char(now(), 'YYYY-MM-DD'))
where not exists (select 1 from public.employees where role = 'hr');

select staff_no as "No. staf", activation_code as "Kod aktivasi (simpan ini)" from public.employees where role = 'hr' and user_id is null;
