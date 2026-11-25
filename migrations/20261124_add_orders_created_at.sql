-- Lulistrack 3.0: fecha real de creación de pedidos.
-- Ejecutar una sola vez en Supabase SQL Editor.
-- Las filas antiguas permanecen en NULL para no asignarles una fecha ficticia.
ALTER TABLE public.orders
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NULL;

-- Solo los pedidos insertados después de esta migración reciben fecha automática.
ALTER TABLE public.orders
  ALTER COLUMN created_at SET DEFAULT NOW();

CREATE INDEX IF NOT EXISTS ix_orders_created_at
  ON public.orders (created_at DESC);
