-- Lulistrack 3.0: prioridad de pedidos y folio automático.
-- Ejecutar una sola vez en Supabase SQL Editor antes de desplegar el backend.

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS is_priority BOOLEAN NOT NULL DEFAULT FALSE;

CREATE SEQUENCE IF NOT EXISTS order_tracking_number_seq
START WITH 1
INCREMENT BY 1
NO MINVALUE
NO MAXVALUE
CACHE 1;
