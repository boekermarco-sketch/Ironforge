-- Stand Doku: 2026-04-22
-- Ziel: ifl_device_catalog für anon lesbar machen (Matrix/eGym/gym80 sichtbar).
-- Im Supabase SQL Editor ausführen.

ALTER TABLE IF EXISTS public.ifl_device_catalog ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ifl_device_catalog_select_anon ON public.ifl_device_catalog;

CREATE POLICY ifl_device_catalog_select_anon
ON public.ifl_device_catalog
FOR SELECT
TO anon
USING (true);
