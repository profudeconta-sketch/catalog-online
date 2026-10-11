-- Run ONCE as Neon owner in the dedicated Neluțu database.
-- Additive migration: preserves used and the singleton row. No reset.
BEGIN;
ALTER TABLE public.nelutu_gemini_budget
  ADD COLUMN IF NOT EXISTS budget_day date
    NOT NULL DEFAULT ((now() AT TIME ZONE 'America/Los_Angeles')::date),
  ADD COLUMN IF NOT EXISTS minute_window timestamptz
    NOT NULL DEFAULT date_trunc('minute', now()),
  ADD COLUMN IF NOT EXISTS minute_used integer NOT NULL DEFAULT 0;
GRANT USAGE ON SCHEMA public TO nelutu_test_runner;
GRANT SELECT, UPDATE ON public.nelutu_gemini_budget TO nelutu_test_runner;
COMMIT;
