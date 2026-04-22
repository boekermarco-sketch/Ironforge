-- Supabase Security Hardening (2026-04-22)
-- Ziel:
-- 1) RLS auf ALLEN Tabellen im public-Schema erzwingen
-- 2) Anon/Authenticated Standardrechte auf public-Tabellen entziehen
-- 3) Nur ifl_device_catalog read-only fuer anon freigeben
--
-- Im Supabase SQL Editor ausfuehren.

BEGIN;

-- ---------------------------------------------------------------------------
-- 0) Sicherheitsnetz: Schema-Nutzung fuer API-Rollen
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- ---------------------------------------------------------------------------
-- 1) RLS auf allen "echten" public-Tabellen aktivieren
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename NOT LIKE 'pg_%'
      AND tablename NOT LIKE 'sql_%'
  LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', r.tablename);
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 2) Standard-Privilegien hart entziehen (Tabellen)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
  LOOP
    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon;', r.tablename);
    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM authenticated;', r.tablename);
  END LOOP;
END $$;

-- Optional: Sequenzen ebenfalls sperren
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT sequence_name
    FROM information_schema.sequences
    WHERE sequence_schema = 'public'
  LOOP
    EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM anon;', r.sequence_name);
    EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM authenticated;', r.sequence_name);
  END LOOP;
END $$;

-- ---------------------------------------------------------------------------
-- 3) Katalog explizit read-only fuer anon erlauben
-- ---------------------------------------------------------------------------
-- Falls alte Policies existieren, zuerst aufraeumen
DROP POLICY IF EXISTS ifl_device_catalog_select_anon ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_select_authenticated ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_insert_anon ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_update_anon ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_delete_anon ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_insert_authenticated ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_update_authenticated ON public.ifl_device_catalog;
DROP POLICY IF EXISTS ifl_device_catalog_delete_authenticated ON public.ifl_device_catalog;

-- Tabellenrechte: nur SELECT fuer API-Rollen
GRANT SELECT ON TABLE public.ifl_device_catalog TO anon, authenticated;

CREATE POLICY ifl_device_catalog_select_anon
ON public.ifl_device_catalog
FOR SELECT
TO anon
USING (true);

CREATE POLICY ifl_device_catalog_select_authenticated
ON public.ifl_device_catalog
FOR SELECT
TO authenticated
USING (true);

-- ---------------------------------------------------------------------------
-- 4) OPTIONALER Self-Check (nach Ausfuehrung separat laufen lassen)
-- ---------------------------------------------------------------------------
-- Welche public-Tabellen haben RLS aus?
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname='public'
-- ORDER BY tablename;
--
-- Welche Policies existieren?
-- SELECT schemaname, tablename, policyname, roles, cmd
-- FROM pg_policies
-- WHERE schemaname='public'
-- ORDER BY tablename, policyname;

COMMIT;
