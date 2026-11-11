-- SPEC-003 (2026-11-11): exact money, ISO 4217 currency, workspace-defined scope (investments).
-- Amounts move from double precision to numeric; currency codes must be three upper-case letters;
-- owner_scope (the owner's own life areas) becomes scope, a free label each workspace defines.
-- Append-only: do not edit once applied.

-- investment
ALTER TABLE investments.investments NO FORCE ROW LEVEL SECURITY;
UPDATE investments.investments SET currency = upper(btrim(currency));
ALTER TABLE investments.investments FORCE ROW LEVEL SECURITY;
ALTER TABLE investments.investments RENAME COLUMN owner_scope TO scope;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.investments'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.investments'::regclass AND attname = 'scope')] LOOP EXECUTE format('ALTER TABLE investments.investments DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.investments ALTER COLUMN scope SET DEFAULT '';
ALTER TABLE investments.investments ADD CONSTRAINT investments_scope_check CHECK (length(scope) <= 64);
DO $$ DECLARE i text; BEGIN SELECT indexname INTO i FROM pg_indexes WHERE schemaname = 'investments' AND tablename = 'investments' AND indexdef LIKE '%(workspace_id, scope)'; IF i IS NOT NULL THEN EXECUTE format('ALTER INDEX investments.%I RENAME TO investments_scope', i); END IF; END $$;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.investments'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.investments'::regclass AND attname = 'quantity')] LOOP EXECUTE format('ALTER TABLE investments.investments DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.investments ALTER COLUMN quantity TYPE numeric(30,10) USING quantity::numeric(30,10);
ALTER TABLE investments.investments ADD CONSTRAINT investments_quantity_check CHECK (quantity IS NULL OR (quantity >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.investments'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.investments'::regclass AND attname = 'cost_basis')] LOOP EXECUTE format('ALTER TABLE investments.investments DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.investments ALTER COLUMN cost_basis TYPE numeric(19,4) USING cost_basis::numeric(19,4);
ALTER TABLE investments.investments ADD CONSTRAINT investments_cost_basis_check CHECK (cost_basis IS NULL OR (cost_basis >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.investments'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.investments'::regclass AND attname = 'current_value')] LOOP EXECUTE format('ALTER TABLE investments.investments DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.investments ALTER COLUMN current_value TYPE numeric(19,4) USING current_value::numeric(19,4);
ALTER TABLE investments.investments ADD CONSTRAINT investments_current_value_check CHECK (current_value IS NULL OR (current_value >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.investments'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.investments'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE investments.investments DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.investments ADD CONSTRAINT investments_currency_check CHECK (currency ~ '^[A-Z]{3}$');

-- market-price
ALTER TABLE investments.market_price_snapshots NO FORCE ROW LEVEL SECURITY;
UPDATE investments.market_price_snapshots SET currency = upper(btrim(currency));
ALTER TABLE investments.market_price_snapshots FORCE ROW LEVEL SECURITY;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.market_price_snapshots'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.market_price_snapshots'::regclass AND attname = 'price')] LOOP EXECUTE format('ALTER TABLE investments.market_price_snapshots DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.market_price_snapshots ALTER COLUMN price TYPE numeric(30,10) USING price::numeric(30,10);
ALTER TABLE investments.market_price_snapshots ADD CONSTRAINT market_price_snapshots_price_check CHECK (price >= 0);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.market_price_snapshots'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.market_price_snapshots'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE investments.market_price_snapshots DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.market_price_snapshots ADD CONSTRAINT market_price_snapshots_currency_check CHECK (currency ~ '^[A-Z]{3}$');

-- valuation
ALTER TABLE investments.valuation_snapshots NO FORCE ROW LEVEL SECURITY;
UPDATE investments.valuation_snapshots SET currency = upper(btrim(currency));
ALTER TABLE investments.valuation_snapshots FORCE ROW LEVEL SECURITY;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.valuation_snapshots'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.valuation_snapshots'::regclass AND attname = 'quantity')] LOOP EXECUTE format('ALTER TABLE investments.valuation_snapshots DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.valuation_snapshots ALTER COLUMN quantity TYPE numeric(30,10) USING quantity::numeric(30,10);
ALTER TABLE investments.valuation_snapshots ADD CONSTRAINT valuation_snapshots_quantity_check CHECK (quantity IS NULL OR (quantity >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.valuation_snapshots'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.valuation_snapshots'::regclass AND attname = 'market_value')] LOOP EXECUTE format('ALTER TABLE investments.valuation_snapshots DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.valuation_snapshots ALTER COLUMN market_value TYPE numeric(19,4) USING market_value::numeric(19,4);
ALTER TABLE investments.valuation_snapshots ADD CONSTRAINT valuation_snapshots_market_value_check CHECK (market_value IS NULL OR (market_value >= 0));
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'investments.valuation_snapshots'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'investments.valuation_snapshots'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE investments.valuation_snapshots DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE investments.valuation_snapshots ADD CONSTRAINT valuation_snapshots_currency_check CHECK (currency ~ '^[A-Z]{3}$');
