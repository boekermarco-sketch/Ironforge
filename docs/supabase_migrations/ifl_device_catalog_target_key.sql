-- Stand Doku: 2026-04-18 14:27 MEZ
-- Einmalig in Supabase SQL Editor ausführen (nach bestehender Tabelle ifl_device_catalog).
-- Ergänzt kanonische Filterfelder für einheitliche Katalog-API / Training-App.

ALTER TABLE ifl_device_catalog ADD COLUMN IF NOT EXISTS target_key TEXT;
ALTER TABLE ifl_device_catalog ADD COLUMN IF NOT EXISTS session_type TEXT;

-- Danach: lokalen Katalog-Sync erneut ausführen (leert Tabelle und füllt neu), damit die Spalten befüllt werden.
