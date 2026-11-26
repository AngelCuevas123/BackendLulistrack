-- Direcciones nacionales estructuradas para pedidos Lulistrack
ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS postal_code VARCHAR(5),
    ADD COLUMN IF NOT EXISTS state VARCHAR(100),
    ADD COLUMN IF NOT EXISTS municipality VARCHAR(120),
    ADD COLUMN IF NOT EXISTS locality VARCHAR(150),
    ADD COLUMN IF NOT EXISTS street VARCHAR(180),
    ADD COLUMN IF NOT EXISTS exterior_number VARCHAR(30),
    ADD COLUMN IF NOT EXISTS interior_number VARCHAR(30),
    ADD COLUMN IF NOT EXISTS address_references TEXT;

CREATE INDEX IF NOT EXISTS idx_orders_postal_code ON orders(postal_code);
