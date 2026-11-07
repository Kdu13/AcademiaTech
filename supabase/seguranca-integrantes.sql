-- O Django usa a service role key somente no servidor. Visitantes consultam
-- os integrantes através das páginas Django, sem acesso de escrita direto.
alter table public.integrantes enable row level security;

do $$
declare
  policy_record record;
  sequence_name text;
begin
  for policy_record in
    select policyname
    from pg_policies
    where schemaname = 'public' and tablename = 'integrantes'
  loop
    execute format('drop policy if exists %I on public.integrantes', policy_record.policyname);
  end loop;

  sequence_name := pg_get_serial_sequence('public.integrantes', 'id');
  if sequence_name is not null then
    execute format('revoke all privileges on sequence %s from public, anon, authenticated', sequence_name);
    execute format('grant usage, select, update on sequence %s to service_role', sequence_name);
  end if;
end $$;

revoke all privileges on table public.integrantes from public, anon, authenticated;
grant select, insert, update, delete on table public.integrantes to service_role;
